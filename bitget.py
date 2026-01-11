"""
Bitget 招聘页面爬虫 (Mokahr 平台)
URL: https://hire-r1.mokahr.com/social-recruitment/bitget/100004136
"""
import asyncio
import aiohttp
from playwright.async_api import async_playwright
from typing import List, Dict


async def scrape_bitget_api() -> List[Dict]:
    """尝试通过 Mokahr API 抓取"""
    jobs = []
    # Mokahr 通常有这样的 API 格式
    api_url = "https://hire-r1.mokahr.com/api-platform/v1/social-recruitment/bitget/100004136/jobs"

    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://hire-r1.mokahr.com/social-recruitment/bitget/100004136"
            }

            # 尝试多个可能的 API 端点
            api_endpoints = [
                "https://hire-r1.mokahr.com/api-platform/v1/social-recruitment/bitget/100004136/jobs",
                "https://hire-r1.mokahr.com/api/v1/jobs",
            ]

            for api in api_endpoints:
                try:
                    async with session.get(api, headers=headers, timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if isinstance(data, list):
                                for item in data:
                                    jobs.append({
                                        "title": item.get("name", item.get("title", "")),
                                        "location": item.get("city", item.get("location", "")),
                                        "team": item.get("department", item.get("team", "")),
                                        "url": f"https://hire-r1.mokahr.com/social-recruitment/bitget/100004136#/job/{item.get('id', '')}",
                                        "company": "Bitget"
                                    })
                            elif isinstance(data, dict) and "data" in data:
                                for item in data["data"]:
                                    jobs.append({
                                        "title": item.get("name", item.get("title", "")),
                                        "location": item.get("city", item.get("location", "")),
                                        "team": item.get("department", item.get("team", "")),
                                        "url": f"https://hire-r1.mokahr.com/social-recruitment/bitget/100004136#/job/{item.get('id', '')}",
                                        "company": "Bitget"
                                    })
                            if jobs:
                                break
                except Exception:
                    continue
    except Exception as e:
        print(f"Bitget API 抓取失败: {e}")

    return jobs


async def scrape_bitget_browser() -> List[Dict]:
    """通过浏览器抓取 Bitget 招聘信息"""
    jobs = []
    url = "https://hire-r1.mokahr.com/social-recruitment/bitget/100004136?locale=en-US#/jobs"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # 等待职位列表加载
            await asyncio.sleep(3)

            # Mokahr 平台通常的职位列表选择器
            await page.wait_for_selector('[class*="job"], [class*="position"], .recruitment-jobs', timeout=30000)

            # 滚动加载更多
            for _ in range(15):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)

            # 获取所有职位卡片
            job_cards = await page.query_selector_all('[class*="job-card"], [class*="job-item"], [class*="position-item"], .job-list-item, a[href*="#/job/"]')

            for card in job_cards:
                try:
                    text = await card.inner_text()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]

                    if not lines:
                        continue

                    title = lines[0]
                    location = ""
                    team = ""

                    # 解析地点和部门
                    for line in lines[1:]:
                        line_lower = line.lower()
                        if any(loc in line_lower for loc in ["hong kong", "singapore", "remote", "beijing", "shanghai", "shenzhen", "taipei", "tokyo"]):
                            location = line
                        elif not team and len(line) > 2:
                            team = line

                    # 获取链接
                    link = await card.get_attribute("href")
                    if not link:
                        link_elem = await card.query_selector("a")
                        if link_elem:
                            link = await link_elem.get_attribute("href")

                    if link and not link.startswith("http"):
                        link = f"https://hire-r1.mokahr.com{link}"

                    if title and len(title) > 2:
                        jobs.append({
                            "title": title,
                            "location": location or "Not specified",
                            "team": team,
                            "url": link or url,
                            "company": "Bitget"
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"Bitget 浏览器抓取出错: {e}")
        finally:
            await browser.close()

    return jobs


async def scrape_bitget() -> List[Dict]:
    """抓取 Bitget 招聘信息，优先使用 API，失败则用浏览器"""
    # 先尝试 API
    jobs = await scrape_bitget_api()

    # 如果 API 失败，使用浏览器
    if not jobs:
        jobs = await scrape_bitget_browser()

    # 去重
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = (job["title"], job.get("location", ""))
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs


if __name__ == "__main__":
    jobs = asyncio.run(scrape_bitget())
    print(f"找到 {len(jobs)} 个职位")
    for job in jobs[:5]:
        print(job)
