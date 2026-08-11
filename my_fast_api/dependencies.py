from fastapi import Depends
from redis.asyncio import Redis

from my_fast_api.config import Settings, get_settings
from my_fast_api.infrastructure.redis import get_redis_client
from my_fast_api.infrastructure.services.jwt_service import JwtService
from my_fast_api.infrastructure.services.rate_limit import RateLimiter


async def get_jwt_service(
    settings: Settings = Depends(get_settings)
) -> JwtService:
    return JwtService(settings)


async def get_rate_limiter(
    redis: Redis = Depends(get_redis_client)
) -> RateLimiter:
    return RateLimiter(redis)
