"""
Job Aggregator - 招聘信息聚合工具

筛选条件:
1. 地点在香港
2. 面向应届生且地点不在中国大陆
"""
import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict

from scraper import scrape_binance, scrape_okx, scrape_bitget


# 中国大陆城市关键词（用于排除）
MAINLAND_CHINA_KEYWORDS = [
    "beijing", "shanghai", "shenzhen", "guangzhou", "hangzhou",
    "chengdu", "nanjing", "wuhan", "xian", "suzhou", "tianjin",
    "chongqing", "dongguan", "foshan", "ningbo", "qingdao",
    "北京", "上海", "深圳", "广州", "杭州", "成都", "南京",
    "武汉", "西安", "苏州", "天津", "重庆", "东莞", "佛山",
    "宁波", "青岛", "mainland china", "china mainland", "中国大陆"
]

# 香港关键词
HONG_KONG_KEYWORDS = ["hong kong", "hongkong", "hk", "香港"]

# 应届生/校招关键词
GRADUATE_KEYWORDS = [
    "graduate", "new grad", "new graduate", "fresh graduate",
    "entry level", "entry-level", "junior", "campus",
    "university", "intern to full", "graduate program",
    "应届", "校招", "毕业生", "实习转正", "管培"
]


def is_in_hong_kong(location: str) -> bool:
    """检查是否在香港"""
    location_lower = location.lower()
    return any(kw in location_lower for kw in HONG_KONG_KEYWORDS)


def is_in_mainland_china(location: str) -> bool:
    """检查是否在中国大陆"""
    location_lower = location.lower()
    return any(kw in location_lower for kw in MAINLAND_CHINA_KEYWORDS)


def is_graduate_position(title: str, team: str = "") -> bool:
    """检查是否是应届生/校招职位"""
    text = f"{title} {team}".lower()
    return any(kw in text for kw in GRADUATE_KEYWORDS)


def filter_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    筛选职位:
    条件1: 地点在香港
    条件2: 面向应届生且地点不在中国大陆

    满足任一条件即可
    """
    filtered = []

    for job in jobs:
        location = job.get("location", "")
        title = job.get("title", "")
        team = job.get("team", "")

        # 条件1: 香港职位
        if is_in_hong_kong(location):
            job["match_reason"] = "Location: Hong Kong"
            filtered.append(job)
            continue

        # 条件2: 应届生职位且不在大陆
        if is_graduate_position(title, team) and not is_in_mainland_china(location):
            job["match_reason"] = "Graduate position (non-mainland)"
            filtered.append(job)
            continue

    return filtered


def generate_html(jobs: List[Dict], output_path: str):
    """生成 HTML 展示页面"""
    # 按公司分组
    jobs_by_company = {}
    for job in jobs:
        company = job.get("company", "Unknown")
        if company not in jobs_by_company:
            jobs_by_company[company] = []
        jobs_by_company[company].append(job)

    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Jobs - HK & Graduate Positions</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #050505;
            --card-bg: #0a0a0a;
            --card-border: #1f1f1f;
            --text-primary: #ededed;
            --text-secondary: #a1a1aa;
            --accent-start: #3b82f6;
            --accent-end: #8b5cf6;
            --hover-border: #3f3f46;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.08), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.08), transparent 25%);
            min-height: 100vh;
            color: var(--text-primary);
            padding: 40px 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 60px;
            position: relative;
        }}

        h1 {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 3.5rem;
            font-weight: 700;
            letter-spacing: -0.05em;
            background: linear-gradient(135deg, #fff 30%, #a1a1aa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 16px;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
            max-width: 600px;
            margin: 0 auto;
        }}

        .update-time {{
            display: inline-block;
            margin-top: 16px;
            padding: 4px 12px;
            border-radius: 9999px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            color: #71717a;
            font-size: 0.75rem;
            font-family: 'Space Grotesk', sans-serif;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 60px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }}

        .stat-item {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--card-border);
            padding: 24px;
            border-radius: 16px;
            text-align: center;
            transition: all 0.3s ease;
        }}

        .stat-item:hover {{
            border-color: var(--hover-border);
            transform: translateY(-2px);
        }}

        .stat-number {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 4px;
        }}

        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .filters {{
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 50px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 10px 24px;
            border: 1px solid var(--card-border);
            border-radius: 9999px;
            background: transparent;
            color: var(--text-secondary);
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .filter-btn:hover {{
            border-color: #fff;
            color: #fff;
        }}

        .filter-btn.active {{
            background: #fff;
            color: #000;
            border-color: #fff;
        }}

        .company-section {{
            margin-bottom: 60px;
            animation: fadeIn 0.5s ease-out;
        }}

        .company-header {{
            display: flex;
            align-items: baseline;
            gap: 16px;
            margin-bottom: 24px;
            padding-left: 8px;
            border-left: 2px solid var(--accent-start);
        }}

        .company-name {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.75rem;
            color: #fff;
            font-weight: 600;
        }}

        .company-count {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}

        .job-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 20px;
        }}

        .job-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .job-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(139, 92, 246, 0.05));
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .job-card:hover {{
            transform: translateY(-4px);
            border-color: var(--hover-border);
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
        }}

        .job-card:hover::before {{
            opacity: 1;
        }}

        .job-title {{
            font-size: 1.1rem;
            font-weight: 500;
            margin-bottom: 16px;
            line-height: 1.4;
            position: relative;
            z-index: 1;
        }}

        .job-title a {{
            color: #fff;
            text-decoration: none;
            transition: color 0.2s;
        }}

        .job-title a:hover {{
            color: #60a5fa;
        }}

        .job-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            position: relative;
            z-index: 1;
            margin-top: auto;
        }}

        .job-tag {{
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 500;
            letter-spacing: 0.02em;
        }}

        .tag-location {{
            background: rgba(59, 130, 246, 0.1);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.2);
        }}

        .tag-team {{
            background: rgba(139, 92, 246, 0.1);
            color: #a78bfa;
            border: 1px solid rgba(139, 92, 246, 0.2);
        }}

        .tag-reason {{
            background: rgba(16, 185, 129, 0.1);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }}

        .no-jobs {{
            text-align: center;
            padding: 80px 20px;
            color: var(--text-secondary);
        }}

        footer {{
            text-align: center;
            padding: 60px 20px;
            color: #52525b;
            font-size: 0.875rem;
            border-top: 1px solid var(--card-border);
            margin-top: 60px;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @media (max-width: 768px) {{
            h1 {{ font-size: 2.5rem; }}
            .stats {{ grid-template-columns: 1fr; }}
            .container {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Crypto Jobs Aggregator</h1>
            <p class="subtitle">Hong Kong & Graduate Positions | Binance, OKX, Bitget</p>
            <p class="update-time">Last updated: {update_time}</p>
        </header>

        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{len(jobs)}</div>
                <div class="stat-label">Total Positions</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len([j for j in jobs if 'Hong Kong' in j.get('match_reason', '')])}</div>
                <div class="stat-label">Hong Kong</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len([j for j in jobs if 'Graduate' in j.get('match_reason', '')])}</div>
                <div class="stat-label">Graduate</div>
            </div>
        </div>

        <div class="filters">
            <button class="filter-btn active" onclick="filterJobs('all')">All</button>
            <button class="filter-btn" onclick="filterJobs('hk')">Hong Kong</button>
            <button class="filter-btn" onclick="filterJobs('graduate')">Graduate</button>
'''

    # 添加公司筛选按钮
    for company in jobs_by_company.keys():
        html_content += f'            <button class="filter-btn" onclick="filterJobs(\'{company.lower()}\')">{company}</button>\n'

    html_content += '''        </div>

        <main id="jobs-container">
'''

    if not jobs:
        html_content += '''            <div class="no-jobs">
                <h2>No matching jobs found</h2>
                <p>Check back later for new opportunities</p>
            </div>
'''
    else:
        for company, company_jobs in jobs_by_company.items():
            html_content += f'''            <div class="company-section" data-company="{company.lower()}">
                <div class="company-header">
                    <h2 class="company-name">{company}</h2>
                    <span class="company-count">{len(company_jobs)} positions</span>
                </div>
                <div class="job-grid">
'''
            for job in company_jobs:
                reason_class = "hk" if "Hong Kong" in job.get("match_reason", "") else "graduate"
                html_content += f'''                    <div class="job-card" data-type="{reason_class}">
                        <h3 class="job-title">
                            <a href="{job.get('url', '#')}" target="_blank" rel="noopener">{job.get('title', 'Unknown Position')}</a>
                        </h3>
                        <div class="job-meta">
                            <span class="job-tag tag-location">{job.get('location', 'N/A')}</span>
                            {f'<span class="job-tag tag-team">{job.get("team")}</span>' if job.get('team') else ''}
                            <span class="job-tag tag-reason">{job.get('match_reason', '')}</span>
                        </div>
                    </div>
'''
            html_content += '''                </div>
            </div>
'''

    html_content += '''        </main>

        <footer>
            <p>Auto-updated daily via GitHub Actions</p>
            <p>Data sourced from official career pages</p>
        </footer>
    </div>

    <script>
        function filterJobs(type) {
            // Update button states
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.textContent.toLowerCase() === type ||
                    (type === 'all' && btn.textContent === 'All') ||
                    (type === 'hk' && btn.textContent === 'Hong Kong') ||
                    (type === 'graduate' && btn.textContent === 'Graduate')) {
                    btn.classList.add('active');
                }
            });

            // Filter jobs
            const sections = document.querySelectorAll('.company-section');
            const cards = document.querySelectorAll('.job-card');

            if (type === 'all') {
                sections.forEach(s => s.style.display = 'block');
                cards.forEach(c => c.style.display = 'block');
            } else if (type === 'hk' || type === 'graduate') {
                sections.forEach(s => s.style.display = 'block');
                cards.forEach(card => {
                    card.style.display = card.dataset.type === type ? 'block' : 'none';
                });
                // Hide empty sections
                sections.forEach(section => {
                    const visibleCards = section.querySelectorAll('.job-card[style="display: block"]');
                    section.style.display = visibleCards.length > 0 ? 'block' : 'none';
                });
            } else {
                // Company filter
                sections.forEach(section => {
                    section.style.display = section.dataset.company === type ? 'block' : 'none';
                });
                cards.forEach(c => c.style.display = 'block');
            }
        }
    </script>
</body>
</html>'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


async def main():
    """主函数"""
    print("=" * 50)
    print("Job Aggregator - Starting...")
    print("=" * 50)

    # 确保输出目录存在
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # 并发抓取所有网站
    print("\n[1/4] Scraping job listings...")

    results = await asyncio.gather(
        scrape_binance(),
        scrape_okx(),
        scrape_bitget(),
        return_exceptions=True
    )

    all_jobs = []
    scrapers = ["Binance", "OKX", "Bitget"]

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"  - {scrapers[i]}: Error - {result}")
        else:
            print(f"  - {scrapers[i]}: {len(result)} jobs found")
            all_jobs.extend(result)

    print(f"\n[2/4] Total jobs scraped: {len(all_jobs)}")

    # 筛选
    print("\n[3/4] Filtering jobs...")
    filtered_jobs = filter_jobs(all_jobs)
    print(f"  - Matching jobs: {len(filtered_jobs)}")
    print(f"    - Hong Kong: {len([j for j in filtered_jobs if 'Hong Kong' in j.get('match_reason', '')])}")
    print(f"    - Graduate (non-mainland): {len([j for j in filtered_jobs if 'Graduate' in j.get('match_reason', '')])}")

    # 保存结果
    print("\n[4/4] Generating output files...")

    # JSON
    json_path = os.path.join(output_dir, "jobs.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "update_time": datetime.now().isoformat(),
            "total_count": len(filtered_jobs),
            "jobs": filtered_jobs
        }, f, ensure_ascii=False, indent=2)
    print(f"  - JSON: {json_path}")

    # HTML
    html_path = os.path.join(output_dir, "index.html")
    generate_html(filtered_jobs, html_path)
    print(f"  - HTML: {html_path}")

    print("\n" + "=" * 50)
    print("Done!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
