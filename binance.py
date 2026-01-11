"""
Binance 招聘页面爬虫
URL: https://www.binance.com/en/careers/job-openings
"""
import asyncio
from playwright.async_api import async_playwright
from typing import List, Dict
import re


async def scrape_binance() -> List[Dict]:
    """抓取 Binance 招聘信息"""
    jobs = []
    url = "https://www.binance.com/en/careers/job-openings?team=All"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # 等待页面加载，使用更通用的选择器
            await asyncio.sleep(5)

            # 尝试多种选择器
            selectors_to_try = [
                'a[href*="/careers/"][href*="detail"]',
                'a[href*="/en/careers/"]',
                '[data-testid*="job"]',
                '.job-item',
                '[class*="position"]',
            ]

            # 滚动加载所有职位
            for _ in range(10):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

            # 再等待一下确保加载完成
            await asyncio.sleep(2)

            # 尝试不同的选择器获取职位
            job_elements = []
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        job_elements = elements
                        break
                except Exception:
                    continue

            # 如果上面的选择器都没找到，尝试获取所有 careers 链接
            if not job_elements:
                job_elements = await page.query_selector_all('a[href*="/careers/"]')

            for elem in job_elements:
                try:
                    href = await elem.get_attribute("href")
                    if not href:
                        continue
                    # 过滤非职位链接
                    if any(x in href for x in ["/job-openings", "/team", "/culture", "/benefits", "/life"]):
                        continue

                    text_content = await elem.inner_text()
                    lines = [l.strip() for l in text_content.split('\n') if l.strip()]

                    if len(lines) >= 1 and len(lines[0]) > 3:
                        title = lines[0]
                        location = lines[1] if len(lines) > 1 else ""
                        team = lines[2] if len(lines) > 2 else ""

                        # 构建完整URL
                        if href.startswith("/"):
                            href = f"https://www.binance.com{href}"

                        jobs.append({
                            "title": title,
                            "location": location,
                            "team": team,
                            "url": href,
                            "company": "Binance"
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"Binance 抓取出错: {e}")
        finally:
            await browser.close()

    # 去重
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = (job["title"], job["location"])
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs


if __name__ == "__main__":
    jobs = asyncio.run(scrape_binance())
    print(f"找到 {len(jobs)} 个职位")
    for job in jobs[:5]:
        print(job)
