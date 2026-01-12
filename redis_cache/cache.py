import hashlib
import orjson
from functools import wraps
from typing import Callable, Any
from .logger_config import logger
from aiocache import Cache
from .client import DEPENDENCY_CACHE_KEY_EXCLUDE

redis_cache: Cache | None = None


def set_redis_instance(redis_instance: Cache) -> None:
    """
    Set the Redis cache instance.
    Args:
        redis_instance (Cache): The Redis cache instance.
    """
    global redis_cache
    redis_cache = redis_instance


def generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Function that generate unique cache key based on function name, arguments and keyword arguments.
    """
    # Drop injected dependencies
    clean_kwargs = {
        k: v
        for k, v in kwargs.items()
        if k not in DEPENDENCY_CACHE_KEY_EXCLUDE and v is not None
    }
    
    try:
        # Use orjson with sorted keys for consistent hashing
        # Tuple of (args, sorted_kwargs) ensures unique signature
        data_to_hash = {
            "args": args,
            "kwargs": clean_kwargs
        }
        serialized = orjson.dumps(data_to_hash, option=orjson.OPT_SORT_KEYS)
        hashed = hashlib.blake2b(serialized, digest_size=8).hexdigest()
        return f"{func_name}:{hashed}"
    except Exception:
        # Fallback to simple string representation if orjson fails
        raw = f"{args}:{clean_kwargs}"
        hashed = hashlib.md5(raw.encode()).hexdigest()[:12]
        return f"{func_name}:{hashed}"


def cache(
    expire: int = 60,
    key: str | None = None,
    namespace: str | None = None,
    key_builder: Callable | None = None,
):
    """
    Decorator to cache endpoint responses in Redis with extreme performance.
    Args:
        expire: cache TTL in seconds
        key: optional custom key
        namespace: optional namespace prefix
        key_builder: optional custom function to build cache key
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
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
                cached_bytes = await redis_cache.get(final_key)
                if cached_bytes:
                    return orjson.loads(cached_bytes)
            except Exception as e:
                logger.error(f"Redis GET failed: {e}")

            response = await func(*args, **kwargs)

            try:
                # orjson.dumps returns bytes, which is what Redis stores efficiently
                await redis_cache.set(final_key, orjson.dumps(response), ttl=expire)
            except Exception as e:
                logger.error(f"Redis SET failed: {e}")

            return response

        return wrapper

    return decorator
