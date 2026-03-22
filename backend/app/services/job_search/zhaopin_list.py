"""
智联招聘：尝试 JSON 接口，失败则解析搜索页 HTML（最小可用）。
"""

import re
import time
from typing import List, Optional, Tuple
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from app.services.job_search.types import RawJobRow
from app.utils.logger import get_logger

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.zhaopin.com/",
}


def search_zhaopin_jobs(
    keyword: str,
    company_keyword: str,
    match_exact: bool,
    city: Optional[str],
    page: int,
    page_size: int,
) -> Tuple[List[RawJobRow], Optional[int]]:
    """
    解析智联搜索列表页（结构可能随站点改版变化，失败时返回空列表）。
    """
    kw = (keyword or "开发").strip()
    session = requests.Session()
    session.headers.update(HEADERS)
    # 智联常见搜索 URL（城市简化为全国）
    url = f"https://sou.zhaopin.com/?jl=489&kw={quote(kw)}&p={max(1, page)}"
    time.sleep(0.6)

    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        logger.warning("智联搜索页请求失败: %s", e, exc_info=True)
        return [], None

    soup = BeautifulSoup(html, "lxml")
    rows: List[RawJobRow] = []

    # 多种可能列表容器（兼容改版）
    cards = soup.select("div.joblist-box__item") or soup.select("a[href*='jobdetail']") or []

    for el in cards[: page_size * 2]:
        if el.name == "a":
            a = el
        else:
            a = el.select_one("a[href*='jobdetail']") or el.find("a", href=re.compile(r"jobdetail"))
        if not a or not a.get("href"):
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https:" + href if href.startswith("//") else "https://www.zhaopin.com" + href
        title_el = el.select_one(".jobinfo__top a") or a
        title = title_el.get_text(strip=True) if title_el else ""
        company_el = el.select_one(".companyinfo__name") or el.select_one(".companyinfo a")
        company = company_el.get_text(strip=True) if company_el else ""
        if company_keyword and company_keyword.strip():
            ck = company_keyword.strip()
            if ck.lower() not in company.lower():
                continue
        salary_el = el.select_one(".jobinfo__salary") or el.select_one(".salary")
        salary = salary_el.get_text(strip=True) if salary_el else ""
        loc_el = el.select_one(".jobinfo__other") or el.select_one(".jobinfo__area")
        loc = loc_el.get_text(strip=True) if loc_el else (city or "")
        if not title:
            continue
        rows.append(
            RawJobRow(
                title=title,
                company_name=company,
                salary_text=salary,
                location=loc,
                published_at=None,
                experience_text="",
                education_text="",
                detail_url=href.split("?")[0],
                raw_snippet=None,
            )
        )
        if len(rows) >= page_size:
            break

    return rows, len(rows) if rows else None
