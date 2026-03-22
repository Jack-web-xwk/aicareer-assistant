"""
进程内 TTL 缓存：减少对招聘站重复请求。
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional, Tuple

_cache: Dict[str, Tuple[float, Any]] = {}
_DEFAULT_TTL = 300.0


def cache_key(payload: dict) -> str:
    """规范化查询参数后生成稳定 key"""
    normalized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_cached(key: str, ttl_seconds: float = _DEFAULT_TTL) -> Optional[Any]:
    now = time.monotonic()
    entry = _cache.get(key)
    if not entry:
        return None
    ts, value = entry
    if now - ts > ttl_seconds:
        del _cache[key]
        return None
    return value


def set_cached(key: str, value: Any) -> None:
    _cache[key] = (time.monotonic(), value)


def clear_expired(ttl_seconds: float = _DEFAULT_TTL) -> None:
    now = time.monotonic()
    dead = [k for k, (ts, _) in _cache.items() if now - ts > ttl_seconds]
    for k in dead:
        del _cache[k]
