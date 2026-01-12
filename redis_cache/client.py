from aiocache import caches, Cache
from .logger_config import logger

DEPENDENCY_CACHE_KEY_EXCLUDE: list[str] = []


class RedisCacheInit:
    def __init__(
        self,
        hostname: str = "localhost",
        port: int = 6379,
        timeout: int = 5,
        dependency: list[str] | None = None,
    ):
        """
        Initialize the Redis cache client with the given parameters.
        Args:
            hostname (str): The hostname of the Redis server.
            port (int): The port number of the Redis server.
            timeout (int): The timeout for the Redis connection.
            dependency (list[str]): The list of dependencies to be excluded from the cache key Generation. Includes like db, s3 client, etc.
        """
        self.hostname: str = hostname
        self.port: int = port
        self.timeout: int = timeout
        self.cache: Cache | None = None
        
        global DEPENDENCY_CACHE_KEY_EXCLUDE
        DEPENDENCY_CACHE_KEY_EXCLUDE.clear()
        if dependency:
            DEPENDENCY_CACHE_KEY_EXCLUDE.extend(dependency)

    async def initialize(self) -> Cache | None:
        """
        Initialize the Redis cache client.
        """
        try:
            caches.set_config(
                {
                    "default": {
                        "cache": "aiocache.backends.redis.RedisCache",
                        "endpoint": self.hostname,
                        "port": self.port,
                        "timeout": self.timeout,
                    }
                }
            )

            cache_instance = caches.get("default")
            if not isinstance(cache_instance, Cache):
                logger.error("Failed to get Cache instance from aiocache")
                return None

            self.cache = cache_instance

            try:
                # Test connection
                await self.cache.get("test")
                logger.info("Redis cache connected successfully.")
            except Exception:
                logger.error("Redis is unreachable — running in fallback mode.")
                self.cache = None

        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self.cache = None

        return self.cache
