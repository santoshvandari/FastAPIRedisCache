# FastAPI Redis Caching

A simple and elegant Redis caching solution for FastAPI applications using decorators.

## Features

-  Easy-to-use decorator-based caching
- Automatic cache key generation with dependency filtering
- Customizable TTL (Time To Live)
- Namespace support for organized caching
- Custom cache keys
- Flexible cache clearing (specific keys, namespaces, or all)
- Graceful fallback when Redis is unavailable

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or manually
pip install fastapi uvicorn aiocache redis
```

## Project Structure

```
fastapi_caching/
├── main.py              # Example FastAPI application with 8 endpoints
├── redis_cache/
│   ├── __init__.py      # Package exports
│   ├── cache.py         # Cache decorator with logging
│   ├── clear.py         # Cache clearing utilities
│   └── client.py        # Redis client initialization
├── requirements.txt     # Python dependencies
├── .env.example         # Environment configuration template
└── README.md            # This file
```

## Quick Start

### 1. Start Redis Server

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally and run
redis-server
```

### 2. Run the Application

```bash
uvicorn main:app --reload
```

### 3. Test the Endpoints

Visit `http://localhost:8000/docs` for interactive API documentation.

## Usage Examples

### Basic Setup (Modern Lifespan)

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis_cache import cache, RedisCacheInit, clear_cache
from redis_cache.cache import set_redis_instance as set_cache_instance
from redis_cache.clear import set_redis_instance as set_clear_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_client = RedisCacheInit(
        hostname="localhost",
        port=6379,
        namespace="my_app",
        timeout=5,
        db=0
    )
    cache_instance = await redis_client.initialize()
    
    if cache_instance:
        set_cache_instance(cache_instance)
        set_clear_instance(cache_instance)
    
    yield
    
    # Shutdown
    await redis_client.close()

app = FastAPI(lifespan=lifespan)
```

### Simple Caching

```python
@app.get("/data")
@cache(expire=60)  # Cache for 60 seconds
async def get_data():
    return {"message": "This is cached"}
```

### Caching with Namespace

```python
@app.get("/user/{user_id}")
@cache(expire=300, namespace="users")
async def get_user(user_id: int):
    return {"user_id": user_id, "name": f"User_{user_id}"}
```

### Custom Cache Key

```python
@app.get("/stats")
@cache(expire=180, key="global_stats", namespace="analytics")
async def get_stats():
    return {"total_users": 1000}
```

### Clearing Cache

```python
# Clear specific key in namespace
await clear_cache(key="user_123", namespace="users")

# Clear all keys in namespace
await clear_cache(namespace="users")

# Clear specific key
await clear_cache(key="my_key")

# Clear all cache
await clear_cache()
```

## Configuration Options

### RedisCacheInit Parameters

- `hostname` (str): Redis server hostname (default: "localhost")
- `port` (int): Redis server port (default: 6379)
- `namespace` (str): Global namespace prefix (default: "main")
- `timeout` (int): Connection timeout in seconds (default: 5)
- `db` (int): Redis database number 0-15 (default: 0)

### Cache Decorator Parameters

- `expire` (int): Cache TTL in seconds (default: 60)
- `key` (str, optional): Custom cache key
- `namespace` (str, optional): Namespace prefix for the cache key

## How It Works

1. **Automatic Key Generation**: If no custom key is provided, the decorator generates a unique key based on the function name and arguments (with dependency filtering)
2. **Fallback Mode**: If Redis is unavailable, endpoints continue to work without caching
3. **JSON Serialization**: Responses are automatically serialized/deserialized
4. **Logging**: Debug logs for cache hits/misses, errors are logged with context



## Best Practices

1. **Set appropriate TTL**: Short TTL for frequently changing data, longer for static content
2. **Use namespaces**: Organize related caches for easier management
3. **Monitor Redis**: Keep an eye on memory usage and eviction policies
4. **Test fallback**: Ensure your app works when Redis is down
5. **Clear strategically**: Use namespace clearing for bulk invalidation
6. **Enable debug logging**: Set `LOG_LEVEL=DEBUG` to see cache hits/misses
7. **Handle dependencies**: Use dependency filtering to avoid caching session data

## Troubleshooting

### Redis Connection Failed

- Ensure Redis is running: `redis-cli ping` should return `PONG`
- Check hostname and port in configuration
- Verify firewall rules if Redis is on a remote server
- Check logs for detailed error messages
- Verify the correct database number (default: 0)

### Cache Not Working

- Check logs for Redis initialization messages
- Verify the decorator is applied before the route decorator
- Ensure `set_redis_instance` is called during startup
- Enable debug logging to see cache operations
- Check if namespace is correctly set

### Performance Issues

- Monitor Redis memory usage: `redis-cli info memory`
- Check for large cached values
- Consider using shorter TTLs for less important data
- Use Redis MONITOR command to debug: `redis-cli monitor`
