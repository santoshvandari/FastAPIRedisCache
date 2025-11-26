from aiocache import caches
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class RedisCacheInit:
    """Initialize and manage Redis cache connection"""
    
    def __init__(
        self,
        hostname: str = "localhost",
        port: int = 6379,
        namespace: str = "main",
        timeout: int = 5,
        db: int = 0
    ):
        """
        Initialize Redis cache configuration.
        
        Args:
            hostname: Redis server hostname
            port: Redis server port
            namespace: Global namespace prefix for all keys
            timeout: Connection timeout in seconds
            db: Redis database number (0-15)
        """
        self.hostname = hostname
        self.port = port
        self.namespace = namespace
        self.timeout = timeout
        self.db = db
        self.cache: Optional[Any] = None

    async def initialize(self) -> Optional[Any]:
        """Initialize Redis cache connection with health check"""
        try:
            caches.set_config(
                {
                    "default": {
                        "cache": "aiocache.backends.redis.RedisCache",
                        "endpoint": self.hostname,
                        "port": self.port,
                        "namespace": self.namespace,
                        "timeout": self.timeout,
                        "db": self.db,
                    }
                }
            )

            self.cache = caches.get("default")

            # Health check
            try:
                await self.cache.set("health_check", "ok", ttl=1)
                result = await self.cache.get("health_check")
                if result == "ok":
                    logger.info(
                        f"Redis cache connected successfully at {self.hostname}:{self.port} "
                        f"(db={self.db}, namespace={self.namespace})"
                    )
                else:
                    raise Exception("Health check failed")
            except Exception as e:
                logger.error(
                    f"Redis is unreachable at {self.hostname}:{self.port} — "
                    f"running in fallback mode. Error: {e}"
                )
                self.cache = None

        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self.cache = None

        return self.cache
    
    async def close(self) -> None:
        """Close Redis cache connection"""
        if self.cache:
            try:
                await self.cache.close()
                logger.info("Redis cache connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
