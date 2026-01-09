import hashlib
import json
from functools import wraps
from typing import Callable

from fastapi.logger import logger
from aiocache import Cache

redis_cache: Cache | None = None


def set_redis_instance(redis_instance: Cache) -> None:
    global redis_cache
    redis_cache = redis_instance


def generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    # Drop injected dependencies
    clean_kwargs = {
        k: v
        for k, v in kwargs.items()
        if k not in ("db", "s3_client_public", "s3_client", "qdrant_db")
        and v is not None
    }
    raw = f"{args}:{clean_kwargs}"
    hashed = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"{func_name}:{hashed}"


def cache(expire: int = 60, key: str | None = None, namespace: str | None = None, key_builder: Callable | None = None):
    """
    Decorator to cache endpoint responses in Redis.
    Args:
        expire: cache TTL in seconds
        key: optional custom key
        namespace: optional namespace prefix
        key_builder: optional custom function to build cache key
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # If Redis not initialized → run without cache
            if redis_cache is None:
                return await func(*args, **kwargs)
            if key_builder:
                final_key = key_builder(*args, **kwargs)
            elif key:
                final_key = key
            else:
                final_key = generate_cache_key(func.__name__, args, kwargs)

            if namespace:
                final_key = f"{namespace}:{final_key}"

            try:
                cached_value = await redis_cache.get(final_key)
                if cached_value:
                    return json.loads(cached_value)
            except Exception:
                logger.error("Redis GET failed")

            response = await func(*args, **kwargs)

            try:
                await redis_cache.set(final_key, json.dumps(response), ttl=expire)
            except Exception:
                logger.error("Redis SET failed")

            return response

        return wrapper

    return decorator
