from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import Redis


class RedisManager:
    _instance: Redis | None = None

    @classmethod
    async def connect(cls, redis_url: str) -> Redis:
        if cls._instance is None:
            cls._instance = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                max_connections=50,
            )
        return cls._instance

    @classmethod
    async def disconnect(cls):
        if cls._instance is not None:
            await cls._instance.aclose()
            cls._instance = None

    @classmethod
    async def get_client(cls) -> Redis:
        if cls._instance is None:
            raise RuntimeError("Redis not initialized. Call connect() first.")
        return cls._instance


@asynccontextmanager
async def get_redis_client() -> AsyncGenerator[Redis]:
    client = await RedisManager.get_client()
    yield client
