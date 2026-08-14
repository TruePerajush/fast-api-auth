from functools import lru_cache

from fastapi import Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from my_fast_api.config import Settings, get_settings
from my_fast_api.infrastructure.services.jwt_service import JwtService


def get_limiter() -> Limiter:
    settings = get_settings()
    return Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)


async def get_jwt_service(settings: Settings = Depends(get_settings)) -> JwtService:
    return JwtService(settings)
