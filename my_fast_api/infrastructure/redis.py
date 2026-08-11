from collections.abc import AsyncGenerator

import redis.asyncio as redis
from redis.asyncio import Redis

from my_fast_api.dependencies import get_settings


async def get_redis_client() -> AsyncGenerator[Redis]:
    settings = get_settings()
    client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        max_connections=50,
    )
    try:
        yield client
    finally:
        await client.close()
