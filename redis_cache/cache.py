import hashlib
import json
from functools import wraps
from typing import Optional, Any, Callable
import logging

logger = logging.getLogger(__name__)

redis_cache: Optional[Any] = None


def set_redis_instance(redis_instance: Any) -> None:
    """Set the global Redis cache instance"""
    global redis_cache
    redis_cache = redis_instance


def generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate a cache key from function name and arguments"""
    raw = f"{args}:{kwargs}"
    hashed = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"{func_name}:{hashed}"


def cache(expire: int = 60, key: Optional[str] = None, namespace: Optional[str] = None) -> Callable:
    """
    Decorator to cache endpoint responses in Redis.
    
    Args:
        expire: Cache TTL in seconds (default: 60)
        key: Optional custom cache key
        namespace: Optional namespace prefix for cache key
    
    Returns:
        Decorated function with caching capability
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # If Redis not initialized → run without cache
            if redis_cache is None:
                logger.debug(f"Cache miss (no Redis): {func.__name__}")
                return await func(*args, **kwargs)

            # Generate or use provided cache key
            if key:
                final_key = key
            else:
                final_key = generate_cache_key(func.__name__, args, kwargs)

            # Add namespace prefix if provided
            if namespace:
                final_key = f"{namespace}:{final_key}"

            # Try to get cached value
            try:
                cached_value = await redis_cache.get(final_key)
                if cached_value:
                    logger.debug(f"Cache hit: {final_key}")
                    return json.loads(cached_value)
                logger.debug(f"Cache miss: {final_key}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode cached value for {final_key}: {e}")
            except Exception as e:
                logger.error(f"Redis GET failed for {final_key}: {e}")

            # Execute function and cache result
            response = await func(*args, **kwargs)

            # Store in cache
            try:
                await redis_cache.set(final_key, json.dumps(response), ttl=expire)
                logger.debug(f"Cached: {final_key} (TTL: {expire}s)")
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize response for {final_key}: {e}")
            except Exception as e:
                logger.error(f"Redis SET failed for {final_key}: {e}")

            return response

        return wrapper

    return decorator
