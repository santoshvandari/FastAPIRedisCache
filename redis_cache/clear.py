from typing import Any, List, Optional
import logging

logger = logging.getLogger(__name__)

redis_cache: Optional[Any] = None


def set_redis_instance(redis_instance: Any) -> None:
    """Set the global Redis cache instance for cache clearing"""
    global redis_cache
    redis_cache = redis_instance


async def clear_cache(
    key: Optional[str] = None, namespace: Optional[str] = None
) -> int:
    """
    Clear Redis cache with flexible targeting.
    
    Args:
        key: Specific cache key to delete
        namespace: Namespace pattern to clear
    
    Behaviors:
        - key + namespace → delete one namespaced key
        - key only → delete specific key
        - namespace only → delete all keys in namespace
        - none → clear all cache
    
    Returns:
        Number of keys deleted
    """
    if redis_cache is None:
        logger.warning("Cannot clear cache: Redis not initialized")
        return 0
    
    try:
        deleted_count = 0
        
        if key and namespace:
            namespaced_key = f"{namespace}:{key}"
            result = await redis_cache.delete(namespaced_key)
            deleted_count = 1 if result else 0
            logger.info(f"Cleared cache key: {namespaced_key}")
            return deleted_count

        if key:
            result = await redis_cache.delete(key)
            deleted_count = 1 if result else 0
            logger.info(f"Cleared cache key: {key}")
            return deleted_count

        if namespace:
            pattern = f"{namespace}:*"
            keys: List[str] = await redis_cache.keys(pattern)
            for k in keys:
                await redis_cache.delete(k)
                deleted_count += 1
            logger.info(f"Cleared {deleted_count} keys in namespace: {namespace}")
            return deleted_count
        
        # Clear all cache
        await redis_cache.clear()
        logger.info("Cleared all cache")
        return -1  # Indicates full clear
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise
