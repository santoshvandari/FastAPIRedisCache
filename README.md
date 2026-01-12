# FastAPI Redis Cache

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org)

**FastAPI Redis Cache** is a lightweight, decorator-based middleware designed to make high-performance API development effortless. By wrapping standard FastAPI routes with a simple `@cache()` decorator, developers can reduce database load and slash response times from hundreds of milliseconds to near-instant.

![Project Banner](banner.png)

---

## Key Features

- **Simple Decorator API**: Cache any endpoint with a single `@cache()` decorator.
- **Smart Key Generation**: Automatically handles function arguments, path parameters, and query parameters.
- **Graceful Resilience**: Production-ready "fail-open" logic. If Redis goes down, your API keeps running without caching.
- **Modern Lifespan Pattern**: Uses `asynccontextmanager` for clean resource initialization and cleanup, following latest FastAPI best practices.
- **Namespace Support**: Organize your cache entries into logical groups (e.g., `users`, `products`) for easier management.
- **Flexible Invalidation**: Clear specific keys, entire namespaces, or the whole cache with ease.
- **Dependency Filtering**: Intelligent filtering to exclude non-cacheable dependencies (like DB sessions or S3 clients) from key generation.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/santoshvandari/FastAPIRedisCache.git
cd FastAPIRedisCache

# Install dependencies
pip install -r requirements.txt
```

---

## Quick Start

### 1. Initialize the Cache

Set up the Redis client using the modern FastAPI lifespan pattern in `main.py`:

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis_cache import cache, RedisCacheInit
from redis_cache.cache import set_redis_instance as set_cache_instance
from redis_cache.clear import set_redis_instance as set_clear_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis
    redis_client = RedisCacheInit(
        hostname="localhost",
        port=6379,
        dependency=["db_session", "s3_client"] # Exclude these from cache keys
    )
    cache_instance = await redis_client.initialize()

    if cache_instance:
        set_cache_instance(cache_instance)
        set_clear_instance(cache_instance)

    yield
    # Shutdown logic goes here

app = FastAPI(lifespan=lifespan)
```

### 2. Cache an Endpoint

Just add the `@cache` decorator to your route!

```python
@app.get("/products/{product_id}")
@cache(expire=300, namespace="catalog")
async def get_product(product_id: int):
    # Simulate an expensive database operation
    await asyncio.sleep(1.5)
    return {"id": product_id, "name": "Premium Gadget", "price": 99.99}
```

---

## Usage Guide

### Caching Options

| Parameter     | Type       | Default | Description                                       |
| :------------ | :--------- | :------ | :------------------------------------------------ |
| `expire`      | `int`      | `60`    | Time-to-Live (TTL) in seconds.                    |
| `namespace`   | `str`      | `None`  | Optional prefix to group keys.                    |
| `key`         | `str`      | `None`  | Static key name (overrides automatic generation). |
| `key_builder` | `Callable` | `None`  | Custom function to generate complex keys.         |

### Manual Cache Invalidation

```python
from redis_cache import clear_cache

# Clear a specific key in a namespace
await clear_cache(key="product_123", namespace="catalog")

# Clear an entire namespace
await clear_cache(namespace="catalog")

# Wipe the entire cache
await clear_cache()
```

---

## How It Works

1. **Key Generation**: When a request hits a cached endpoint, `FastCacheRedis` generates a unique MD5 hash based on the function name and its input arguments.
2. **Dependency Exclusion**: It automatically strips out dependencies that are defined in Initialization (like database sessions) from the hash calculation to ensure the same data returns the same key regardless of the session state.
3. **Fallback**: If the Redis server is unreachable, the system catches the exception, logs a warning, and executes the original function directly—ensuring 100% uptime.

---

## Contributing

We welcome contributions from the community! Please follow our [contributing guidelines](CONTRIBUTING.md).

Code of Conduct
Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms.

## License

This project is open-source and available under the MIT License.
