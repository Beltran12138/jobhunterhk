"""
OKX 招聘页面爬虫
URL: https://www.okx.com/zh-hans/join-us/openings
"""
import asyncio
from playwright.async_api import async_playwright
from typing import List, Dict


async def scrape_okx() -> List[Dict]:
    """抓取 OKX 招聘信息"""
    jobs = []
    url = "https://www.okx.com/join-us/openings"  # 使用英文版

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # 等待页面加载
            await asyncio.sleep(3)

            # 尝试点击 "Show all" 或加载更多按钮
            for _ in range(10):
                try:
                    load_more = await page.query_selector('button:has-text("Load more"), button:has-text("Show all"), [class*="load-more"]')
                    if load_more:
                        await load_more.click()
                        await asyncio.sleep(1)
                    else:
                        break
                except Exception:
                    break

            # 滚动加载
            for _ in range(10):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)

            # 获取职位信息 - OKX 通常使用卡片式布局
            job_cards = await page.query_selector_all('[class*="job"], [class*="position"], [class*="opening"], a[href*="/job/"]')

            for card in job_cards:
                try:
                    # 尝试获取链接
                    link = await card.get_attribute("href")
                    if not link:
                        link_elem = await card.query_selector("a")
                        if link_elem:
                            link = await link_elem.get_attribute("href")

                    text = await card.inner_text()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]

                    if len(lines) >= 1:
                        title = lines[0]
                        location = ""
                        team = ""

                        # 尝试从文本中提取地点
                        for line in lines[1:]:
                            if any(loc in line.lower() for loc in ["hong kong", "singapore", "remote", "beijing", "shanghai", "shenzhen"]):
                                location = line
                                break
                            elif not team:
                                team = line

                        if link and link.startswith("/"):
                            link = f"https://www.okx.com{link}"

                        if title and len(title) > 3:
                            jobs.append({
                                "title": title,
                                "location": location or "Not specified",
                                "team": team,
                                "url": link or url,
                                "company": "OKX"
                            })
                except Exception:
                    continue

            # 如果上面的选择器没找到，尝试更通用的方法
            if not jobs:
                all_links = await page.query_selector_all('a[href*="job"], a[href*="position"], a[href*="opening"]')
                for link_elem in all_links:
                    try:
                        href = await link_elem.get_attribute("href")
                        text = await link_elem.inner_text()
                        if text and len(text.strip()) > 3:
                            jobs.append({
                                "title": text.strip().split('\n')[0],
                                "location": "Not specified",
                                "team": "",
                                "url": href if href.startswith("http") else f"https://www.okx.com{href}",
                                "company": "OKX"
                            })
                    except Exception:
                        continue

        except Exception as e:
            print(f"OKX 抓取出错: {e}")
        finally:
            await browser.close()

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
    jobs = asyncio.run(scrape_okx())
    print(f"找到 {len(jobs)} 个职位")
    for job in jobs[:5]:
        print(job)
