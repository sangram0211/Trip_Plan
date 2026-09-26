"""
Redis cache for expensive external calls.

Design notes
------------
* Redis is treated as a pure optimisation. If it is down, unreachable or
  disabled, every decorated function falls through to the real call. A
  cache outage must never take the trip planner down with it.
* Values are stored as JSON (``default=str``) rather than pickled, so a
  compromised or shared Redis can never execute code on deserialisation.
"""

import functools
import hashlib
import json
import logging
import time
from typing import Any, Callable, Optional

import redis

from src.config.settings import (
    CACHE_ENABLED,
    CACHE_KEY_PREFIX,
    CACHE_RECONNECT_SECONDS,
    REDIS_URL,
)

logger = logging.getLogger(__name__)


_client: Optional[redis.Redis] = None
_last_failure: Optional[float] = None


def get_client() -> Optional[redis.Redis]:
    """
    Return a shared Redis client, or None when caching is unavailable.

    A failed connection is retried after CACHE_RECONNECT_SECONDS rather than
    disabling the cache for the life of the process.
    """

    global _client, _last_failure

    if not CACHE_ENABLED:
        return None

    if _client is not None:
        return _client

    now = time.monotonic()

    if _last_failure is not None and now - _last_failure < CACHE_RECONNECT_SECONDS:
        return None

    try:
        client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()

        _client = client
        _last_failure = None
        logger.info("Redis cache connected: %s", REDIS_URL)

    except Exception as error:
        _client = None
        _last_failure = now
        logger.warning(
            "Redis cache unavailable (%s). Continuing without cache.",
            error,
        )

    return _client


def _cache_key(fn_name: str, args: tuple, kwargs: dict) -> str:
    payload = json.dumps({"fn": fn_name, "args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:24]
    return f"{CACHE_KEY_PREFIX}{fn_name}:{digest}"


def async_cached(ttl: int):
    """
    Decorator that caches the return value of an async function in Redis.
    Falls through to the real call if Redis is unavailable.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            client = get_client()
            key = _cache_key(fn.__name__, args, kwargs)

            if client:
                try:
                    cached = client.get(key)
                    if cached is not None:
                        return json.loads(cached)
                except Exception:
                    pass

            result = await fn(*args, **kwargs)

            if client:
                try:
                    client.setex(key, ttl, json.dumps(result, default=str))
                except Exception:
                    pass

            return result

        return wrapper

    return decorator
