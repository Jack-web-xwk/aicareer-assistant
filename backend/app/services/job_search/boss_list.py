"""
Boss 直聘职位列表：调用 wapi 搜索接口（与 job_scraper 请求策略一致）。
"""

import time
from typing import List, Optional, Tuple
from urllib.parse import quote

import requests

from app.services.job_search.types import RawJobRow
from app.utils.logger import get_logger

logger = get_logger(__name__)

BOSS_SEARCH = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.zhipin.com/web/geek/job",
    "Origin": "https://www.zhipin.com",
}

# 常见城市编码（Boss）；未匹配时用全国
_CITY_CODES = {
    "全国": "100010000",
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280100",
    "深圳": "101280600",
    "杭州": "101210100",
    "成都": "101270100",
    "武汉": "101200100",
    "西安": "101110100",
    "南京": "101190100",
}


def _city_code(city: Optional[str]) -> str:
    if not city or not str(city).strip():
        return "100010000"
    c = str(city).strip()
    return _CITY_CODES.get(c, "100010000")


def _walk_job_list(obj) -> List[dict]:
    """从 Boss JSON 中递归查找 jobList 数组。"""
    if isinstance(obj, dict):
        if "jobList" in obj and isinstance(obj["jobList"], list):
            return obj["jobList"]
        for v in obj.values():
            found = _walk_job_list(v)
            if found:
                return found
    elif isinstance(obj, list):
        for it in obj:
            found = _walk_job_list(it)
            if found:
                return found
    return []


def _total_count(obj) -> Optional[int]:
    if isinstance(obj, dict):
        z = obj.get("zpData") or {}
        for key in ("totalCount", "total", "count"):
            if key in z and isinstance(z[key], int):
                return int(z[key])
        for v in obj.values():
            t = _total_count(v)
            if t is not None:
                return t
    return None


def search_boss_jobs(
    keyword: str,
    company_keyword: str,
    match_exact: bool,
    city: Optional[str],
    page: int,
    page_size: int,
) -> Tuple[List[RawJobRow], Optional[int]]:
    """
    返回 (原始行列表, Boss 侧 total 若可解析)。
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    city_code = _city_code(city)
    params = {
        "query": keyword.strip() or "开发",
        "page": max(1, page),
        "pageSize": min(max(1, page_size), 100),
        "city": city_code,
    }
    time.sleep(0.5)

    try:
        r = session.get(BOSS_SEARCH, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning("Boss 职位列表请求失败: %s", e, exc_info=True)
        return [], None

    if data.get("code") not in (0, None) and data.get("code") != 0:
        logger.warning("Boss API 业务码非 0: %s", data.get("code"))
        return [], None

    jobs = _walk_job_list(data)
    total = _total_count(data)
    rows: List[RawJobRow] = []

    for j in jobs:
        if not isinstance(j, dict):
            continue
        title = j.get("jobName") or j.get("title") or ""
        brand = j.get("brandName") or j.get("companyName") or ""
        if company_keyword and company_keyword.strip():
            ck = company_keyword.strip()
            if match_exact:
                if ck.lower() not in (brand or "").lower():
                    continue
            else:
                if ck.lower() not in (brand or "").lower():
                    continue
        salary = j.get("salaryDesc") or j.get("salary") or ""
        loc = j.get("cityName") or j.get("locationName") or ""
        exp = j.get("jobExperience") or ""
        edu = j.get("jobDegree") or ""
        jid = j.get("encryptJobId") or j.get("jobId") or ""
        security = j.get("securityId") or ""
        if not jid:
            continue
        detail = f"https://www.zhipin.com/job_detail/{jid}.html"
        if security:
            detail += f"?securityId={quote(str(security), safe='')}"
        pub = j.get("lastModifyTime") or j.get("updateTime") or j.get("time")
        if pub is not None:
            pub = str(pub)
        rows.append(
            RawJobRow(
                title=str(title),
                company_name=str(brand),
                salary_text=str(salary),
                location=str(loc),
                published_at=pub,
                experience_text=str(exp),
                education_text=str(edu),
                detail_url=detail,
                raw_snippet=None,
            )
        )

    return rows, total
