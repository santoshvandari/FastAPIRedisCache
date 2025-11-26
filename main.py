from fastapi import FastAPI
from redis_cache import cache, RedisCacheInit, clear_cache
from redis_cache.cache import set_redis_instance as set_cache_instance
from redis_cache.clear import set_redis_instance as set_clear_instance
import time

app = FastAPI(title="FastAPI Redis Caching Example")

# Initialize Redis Cache on startup
@app.on_event("startup")
async def startup_event():
    redis_client = RedisCacheInit(
        hostname="localhost",
        port=6379,
        namespace="fastapi_app",
        timeout=5
    )
    cache_instance = await redis_client.initialize()
    
    # Set the Redis instance for both cache and clear_cache functions
    if cache_instance:
        set_cache_instance(cache_instance)
        set_clear_instance(cache_instance)


# Example 1: Basic caching with default TTL (60 seconds)
@app.get("/")
@cache(expire=60)
async def root():
    # Simulate a slow operation
    time.sleep(2)
    return {
        "message": "Hello World",
        "timestamp": time.time(),
        "note": "This response is cached for 60 seconds"
    }


# Example 2: Custom cache key and namespace
@app.get("/user/{user_id}")
@cache(expire=300, namespace="users")
async def get_user(user_id: int):
    # Simulate database query
    time.sleep(1)
    return {
        "user_id": user_id,
        "name": f"User_{user_id}",
        "email": f"user{user_id}@example.com",
        "timestamp": time.time()
    }


# Example 3: Caching with query parameters
@app.get("/products")
@cache(expire=120, namespace="products")
async def get_products(category: str = "all", limit: int = 10):
    # Simulate expensive query
    time.sleep(1.5)
    return {
        "category": category,
        "limit": limit,
        "products": [f"Product_{i}" for i in range(limit)],
        "timestamp": time.time()
    }


# Example 4: Custom cache key
@app.get("/stats")
@cache(expire=180, key="global_stats", namespace="analytics")
async def get_stats():
    time.sleep(2)
    return {
        "total_users": 1000,
        "active_sessions": 42,
        "timestamp": time.time()
    }


# Example 5: Clear specific cache
@app.delete("/cache/clear")
async def clear_specific_cache(key: str = None, namespace: str = None):
    await clear_cache(key=key, namespace=namespace)
    return {
        "status": "success",
        "message": f"Cache cleared for key={key}, namespace={namespace}"
    }


# Example 6: Clear all cache
@app.delete("/cache/clear-all")
async def clear_all_cache():
    await clear_cache()
    return {
        "status": "success",
        "message": "All cache cleared"
    }


# Example 7: Endpoint without caching
@app.get("/no-cache")
async def no_cache_endpoint():
    return {
        "message": "This endpoint is not cached",
        "timestamp": time.time()
    }