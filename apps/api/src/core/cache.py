"""Optional Redis cache for Proxmox Explorer and other list endpoints."""
import json
from typing import Any

from src.config import settings

_redis_client: Any = None
_CACHE_TTL = 300  # 5 minutes


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception:
        _redis_client = False
        return None


def cache_get(key: str) -> Any | None:
    r = _get_redis()
    if not r:
        return None
    try:
        raw = r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl: int = _CACHE_TTL) -> None:
    r = _get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def cache_delete_pattern(prefix: str) -> None:
    r = _get_redis()
    if not r:
        return
    try:
        for k in r.scan_iter(match=f"{prefix}*"):
            r.delete(k)
    except Exception:
        pass
