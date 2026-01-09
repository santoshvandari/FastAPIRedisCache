from aiocache import caches, Cache
from .logger_config import logger


class RedisCacheInit:
    def __init__(self, hostname: str = "localhost", port: int = 6379, timeout: int = 5):
        self.hostname: str = hostname
        self.port: int = port
        self.timeout: int = timeout
        self.cache: Cache | None= None

    async def initialize(self):
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

            self.cache = caches.get("default")

            try:
                await self.cache.get("test")
                logger.info("Redis cache connected successfully.")
            except Exception:
                logger.error("Redis is unreachable — running in fallback mode.")
                self.cache = None

        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self.cache = None

        return self.cache
