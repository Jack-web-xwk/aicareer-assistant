"""
按客户端 IP 的内存滑动窗口限流（用于职位搜索等爬虫类接口）。
"""

import threading
import time
from collections import deque
from typing import Deque, Dict

from fastapi import HTTPException, Request

from app.core.config import settings

_lock = threading.Lock()
_buckets: Dict[str, Deque[float]] = {}


def get_client_ip(request: Request) -> str:
    """优先 X-Forwarded-For 首个地址，否则 Request.client.host。"""
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def check_job_search_rate_limit(request: Request) -> None:
    """每分钟每 IP 最多 JOB_SEARCH_RATE_LIMIT_PER_MINUTE 次，超限 429 + Retry-After。"""
    ip = get_client_ip(request)
    limit = max(1, settings.JOB_SEARCH_RATE_LIMIT_PER_MINUTE)
    window = 60.0
    now = time.monotonic()
    with _lock:
        dq = _buckets.setdefault(ip, deque())
        while dq and now - dq[0] > window:
            dq.popleft()
        if len(dq) >= limit:
            raise HTTPException(
                status_code=429,
                detail="职位搜索请求过于频繁，请稍后再试（每 IP 每分钟限流）。",
                headers={"Retry-After": "60"},
            )
        dq.append(now)
