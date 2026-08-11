from collections.abc import AsyncGenerator
from functools import lru_cache

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from my_fast_api.config import get_settings
from my_fast_api.infrastructure.database import AsyncSessionLocal
from my_fast_api.infrastructure.redis import redis_client
from my_fast_api.infrastructure.services.jwt_service import JwtService
from my_fast_api.infrastructure.services.rate_limit import RateLimiter


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> Redis:
    return redis_client


def get_jwt_service() -> JwtService:
    return JwtService(get_settings())


async def get_rate_limiter() -> RateLimiter:
    from my_fast_api.infrastructure.services.rate_limit import RateLimiter

    redis = await get_redis()
    return RateLimiter(redis)
