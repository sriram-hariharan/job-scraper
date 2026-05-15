from __future__ import annotations

import os
import secrets
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.storage.redis_cache import redis_client, redis_enabled


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _default_lock_ttl_seconds() -> int:
    raw = _clean_text(os.environ.get("JOB_STACK_REDIS_LOCK_TTL_SECONDS"))
    try:
        ttl = int(raw)
    except Exception:
        ttl = 300

    return max(1, min(ttl, 3600))


@dataclass(frozen=True)
class RedisLockHandle:
    key: str
    token: str
    acquired: bool
    ttl_seconds: int


_RELEASE_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
""".strip()


_REFRESH_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("expire", KEYS[1], ARGV[2])
end
return 0
""".strip()


def redis_lock_key(namespace: str, name: str) -> str:
    safe_namespace = _clean_text(namespace)
    safe_name = _clean_text(name)

    if not safe_namespace:
        raise ValueError("lock namespace is required.")
    if not safe_name:
        raise ValueError("lock name is required.")

    return f"lock:{safe_namespace}:{safe_name}"


def acquire_redis_lock(
    key: str,
    *,
    ttl_seconds: Optional[int] = None,
    token: str = "",
) -> RedisLockHandle:
    safe_key = _clean_text(key)
    if not safe_key:
        raise ValueError("lock key is required.")

    ttl = int(ttl_seconds or _default_lock_ttl_seconds())
    ttl = max(1, min(ttl, 3600))
    safe_token = _clean_text(token) or secrets.token_urlsafe(24)

    if not redis_enabled():
        return RedisLockHandle(
            key=safe_key,
            token=safe_token,
            acquired=False,
            ttl_seconds=ttl,
        )

    acquired = bool(
        redis_client().set(
            safe_key,
            safe_token,
            nx=True,
            ex=ttl,
        )
    )

    return RedisLockHandle(
        key=safe_key,
        token=safe_token,
        acquired=acquired,
        ttl_seconds=ttl,
    )


def release_redis_lock(handle: RedisLockHandle) -> bool:
    if not handle or not _clean_text(handle.key) or not _clean_text(handle.token):
        return False

    if not redis_enabled():
        return False

    result = redis_client().eval(
        _RELEASE_LOCK_SCRIPT,
        1,
        handle.key,
        handle.token,
    )
    return int(result or 0) == 1


def refresh_redis_lock(
    handle: RedisLockHandle,
    *,
    ttl_seconds: Optional[int] = None,
) -> bool:
    if not handle or not _clean_text(handle.key) or not _clean_text(handle.token):
        return False

    if not redis_enabled():
        return False

    ttl = int(ttl_seconds or handle.ttl_seconds or _default_lock_ttl_seconds())
    ttl = max(1, min(ttl, 3600))

    result = redis_client().eval(
        _REFRESH_LOCK_SCRIPT,
        1,
        handle.key,
        handle.token,
        ttl,
    )
    return int(result or 0) == 1


def redis_lock_status_payload(key: str) -> Dict[str, Any]:
    safe_key = _clean_text(key)
    if not safe_key:
        return {
            "ok": False,
            "exists": False,
            "ttl_seconds": -2,
            "error": "lock key is required.",
        }

    if not redis_enabled():
        return {
            "ok": False,
            "exists": False,
            "ttl_seconds": -2,
            "error": "REDIS_URL is not configured.",
        }

    try:
        client = redis_client()
        exists = bool(client.exists(safe_key))
        ttl = int(client.ttl(safe_key) or -2)
        return {
            "ok": True,
            "exists": exists,
            "ttl_seconds": ttl,
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "exists": False,
            "ttl_seconds": -2,
            "error": repr(exc),
        }


def wait_for_redis_lock(
    key: str,
    *,
    ttl_seconds: Optional[int] = None,
    wait_seconds: float = 0,
    poll_seconds: float = 0.1,
) -> RedisLockHandle:
    deadline = time.monotonic() + max(0.0, float(wait_seconds or 0))
    poll = max(0.01, min(float(poll_seconds or 0.1), 5.0))

    while True:
        handle = acquire_redis_lock(
            key,
            ttl_seconds=ttl_seconds,
        )
        if handle.acquired:
            return handle

        if time.monotonic() >= deadline:
            return handle

        time.sleep(poll)
