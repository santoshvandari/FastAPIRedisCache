from aiocache import Cache
from .logger_config import logger
from typing import Any

redis_cache: Cache | None = None


def set_redis_instance(redis_instance: Cache) -> None:
    """
    Set the Redis cache instance.
    Args:
        redis_instance (Cache): The Redis cache instance.
    """
    global redis_cache
    redis_cache = redis_instance


async def clear_cache(key: str | None = None, namespace: str | None = None) -> None:
    """
    Clear Redis cache efficiently.
    Uses SCAN instead of KEYS to avoid blocking the Redis server.
    """

    if redis_cache is None:
        logger.warning("Attempted to clear cache but Redis is not initialized.")
        return

    try:
        if key and namespace:
            namespaced_key = f"{namespace}:{key}"
            await redis_cache.delete(namespaced_key)
            logger.info(f"Cleared specific namespaced key: {namespaced_key}")
            return

        if key:
            await redis_cache.delete(key)
            logger.info(f"Cleared specific key: {key}")
            return

        if namespace:
            pattern = f"{namespace}:*"
            raw_client: Any = getattr(
                redis_cache, "client", getattr(redis_cache, "_client", None)
            )
            
            if not raw_client:
                # Fallback if raw client is not accessible
                logger.warning("Raw redis client not found, falling back to clear() - caution: clears everything")
                await redis_cache.clear()
                return

            # Efficiently scan and delete using pipelining
            count = 0
            pipe = raw_client.pipeline()
            async for k in raw_client.scan_iter(match=pattern):
                key_str = k.decode("utf-8") if isinstance(k, bytes) else k
                pipe.delete(key_str)
                count += 1
                
                # Execute in batches of 1000 to avoid memory pressure
                if count % 1000 == 0:
                    await pipe.execute()
                    pipe = raw_client.pipeline()
            
            await pipe.execute()
            logger.info(f"Cleared {count} keys in namespace: {namespace}")
            return

        # Clear everything
        await redis_cache.clear()
        logger.info("Cleared all cache entries.")
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
