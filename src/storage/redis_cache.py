from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict, Optional


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def redis_enabled() -> bool:
    return bool(_clean_text(os.environ.get("REDIS_URL")))


@lru_cache(maxsize=1)
def redis_client():
    redis_url = _clean_text(os.environ.get("REDIS_URL"))
    if not redis_url:
        raise RuntimeError("REDIS_URL is required for Redis cache access.")

    import redis

    return redis.Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )


def redis_ping_payload() -> Dict[str, Any]:
    if not redis_enabled():
        return {
            "ok": False,
            "enabled": False,
            "error": "REDIS_URL is not configured.",
        }

    try:
        pong = redis_client().ping()
        return {
            "ok": bool(pong),
            "enabled": True,
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "enabled": True,
            "error": repr(exc),
        }


def cache_get_json(key: str) -> Optional[Any]:
    safe_key = _clean_text(key)
    if not safe_key or not redis_enabled():
        return None

    raw = redis_client().get(safe_key)
    if raw is None:
        return None

    return json.loads(raw)


def cache_set_json(key: str, value: Any, *, ttl_seconds: int) -> bool:
    safe_key = _clean_text(key)
    if not safe_key or not redis_enabled():
        return False

    ttl = max(1, int(ttl_seconds or 1))
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return bool(redis_client().setex(safe_key, ttl, payload))


def cache_delete(key: str) -> int:
    safe_key = _clean_text(key)
    if not safe_key or not redis_enabled():
        return 0

    return int(redis_client().delete(safe_key) or 0)


def cache_delete_prefix(prefix: str) -> int:
    safe_prefix = _clean_text(prefix)
    if not safe_prefix or not redis_enabled():
        return 0

    client = redis_client()
    deleted = 0

    for key in client.scan_iter(match=f"{safe_prefix}*"):
        deleted += int(client.delete(key) or 0)

    return deleted

