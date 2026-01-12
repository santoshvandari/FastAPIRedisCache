from aiocache import Cache

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
    Clear Redis cache:
        - key only  → delete key
        - namespace only → delete all keys in namespace
        - key + namespace → delete one namespaced key
        - none → clear all cache
    """

    if redis_cache is None:
        return
    try:
        if key and namespace:
            namespaced_key = f"{namespace}:{key}"
            await redis_cache.delete(namespaced_key)
            return

        if key:
            await redis_cache.delete(key)
            return

        if namespace:
            pattern = f"{namespace}:*"
            raw_client = getattr(
                redis_cache, "client", getattr(redis_cache, "_client", None)
            )
            if not raw_client:
                return
            key_bytes_list: list[bytes] = await raw_client.keys(pattern)
            keys_to_delete: list[str] = [k.decode("utf-8") for k in key_bytes_list]
            if keys_to_delete:
                for key_to_delete in keys_to_delete:
                    await redis_cache.delete(key_to_delete)
            return
        await redis_cache.clear()
    except Exception:
        pass
