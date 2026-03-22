"""
鱼泡直聘 / 鱼泡网类站点：关键词搜索列表（最小 HTML 解析，易随站点改版失效）。
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
}


def search_yupao_jobs(
    keyword: str,
    company_keyword: str,
    match_exact: bool,
    city: Optional[str],
    page: int,
    page_size: int,
) -> Tuple[List[RawJobRow], Optional[int]]:
    """
    尝试解析鱼泡招聘搜索（域名与路径可能调整，失败返回空列表）。
    """
    kw = (keyword or "招聘").strip()
    session = requests.Session()
    session.headers.update(HEADERS)
    # 鱼泡常见招聘搜索入口（若 404 则自然返回空）
    url = f"https://www.yupao.com/zhaopin/?keyword={quote(kw)}&page={max(1, page)}"
    time.sleep(0.6)

    try:
        r = session.get(url, timeout=20, allow_redirects=True)
        if r.status_code >= 400:
            logger.info("鱼泡搜索 HTTP %s，跳过", r.status_code)
            return [], None
        html = r.text
    except Exception as e:
        logger.warning("鱼泡搜索请求失败: %s", e, exc_info=True)
        return [], None

    soup = BeautifulSoup(html, "lxml")
    rows: List[RawJobRow] = []

    for a in soup.select("a[href*='job'], a[href*='detail'], a[href*='zhaopin']")[: page_size * 4]:
        href = a.get("href") or ""
        if not href or href.startswith("#"):
            continue
        if not re.search(r"job|detail|zhaopin", href, re.I):
            continue
        if not href.startswith("http"):
            href = "https://www.yupao.com" + href
        title = a.get_text(strip=True)
        if len(title) < 4:
            continue
        parent = a.find_parent(["li", "div", "article"]) or a
        company = ""
        for sel in [".company", ".name", "[class*='company']"]:
            c = parent.select_one(sel)
            if c:
                company = c.get_text(strip=True)
                break
        if company_keyword and company_keyword.strip():
            if company_keyword.strip().lower() not in company.lower():
                continue
        rows.append(
            RawJobRow(
                title=title[:200],
                company_name=company or "（见详情）",
                salary_text="",
                location=city or "",
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
