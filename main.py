from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from redis_cache import cache, RedisCacheInit, clear_cache
from redis_cache.cache import set_redis_instance as set_cache_instance
from redis_cache.clear import set_redis_instance as set_clear_instance
import asyncio
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup Redis cache"""
    # Startup
    redis_client = RedisCacheInit(
        hostname="localhost",
        port=6379,
        namespace="fastapi_app",
        timeout=5
    )
    cache_instance = await redis_client.initialize()
    
    if cache_instance:
        set_cache_instance(cache_instance)
        set_clear_instance(cache_instance)
        logger.info("Redis cache initialized successfully")
    else:
        logger.warning("Running without Redis cache")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")


app = FastAPI(
    title="FastAPI Redis Caching Example",
    version="1.0.0",
    description="Example application demonstrating Redis caching with FastAPI",
    lifespan=lifespan
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint - not cached"""
    return {"status": "healthy", "service": "fastapi-redis-caching"}


# Example 1: Basic caching with default TTL (60 seconds)
@app.get("/")
@cache(expire=60)
async def root():
    """Root endpoint with basic caching"""
    # Simulate a slow operation using async sleep
    await asyncio.sleep(2)
    return {
        "message": "Hello World",
        "timestamp": asyncio.get_event_loop().time(),
        "note": "This response is cached for 60 seconds"
    }


# Example 2: Custom cache key and namespace
@app.get("/user/{user_id}")
@cache(expire=300, namespace="users")
async def get_user(user_id: int):
    """Get user by ID with namespace caching"""
    if user_id < 1:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Simulate database query
    await asyncio.sleep(1)
    return {
        "user_id": user_id,
        "name": f"User_{user_id}",
        "email": f"user{user_id}@example.com",
        "timestamp": asyncio.get_event_loop().time()
    }


# Example 3: Caching with query parameters
@app.get("/products")
@cache(expire=120, namespace="products")
async def get_products(category: str = "all", limit: int = 10):
    """Get products with category and limit filters"""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    # Simulate expensive query
    await asyncio.sleep(1.5)
    return {
        "category": category,
        "limit": limit,
        "products": [f"Product_{i}" for i in range(limit)],
        "timestamp": asyncio.get_event_loop().time()
    }


# Example 4: Custom cache key
@app.get("/stats")
@cache(expire=180, key="global_stats", namespace="analytics")
async def get_stats():
    """Get global statistics with custom cache key"""
    await asyncio.sleep(2)
    return {
        "total_users": 1000,
        "active_sessions": 42,
        "timestamp": asyncio.get_event_loop().time()
    }


# Example 5: Clear specific cache
@app.delete("/cache/clear")
async def clear_specific_cache(key: Optional[str] = None, namespace: Optional[str] = None):
    """Clear specific cache by key and/or namespace"""
    try:
        await clear_cache(key=key, namespace=namespace)
        return {
            "status": "success",
            "message": f"Cache cleared for key={key}, namespace={namespace}"
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


# Example 6: Clear all cache
@app.delete("/cache/clear-all")
async def clear_all_cache():
    """Clear all cache entries"""
    try:
        await clear_cache()
        return {
            "status": "success",
            "message": "All cache cleared"
        }
    except Exception as e:
        logger.error(f"Failed to clear all cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear all cache")


# Example 7: Endpoint without caching
@app.get("/no-cache")
async def no_cache_endpoint():
    """Example endpoint without caching"""
    return {
        "message": "This endpoint is not cached",
        "timestamp": asyncio.get_event_loop().time()
    }