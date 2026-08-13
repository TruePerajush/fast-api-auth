from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from redis import RedisError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from my_fast_api.config import get_settings
from my_fast_api.dependencies import get_limiter
from my_fast_api.features.router import router
from my_fast_api.infrastructure.database import create_tables, init_db_engine
from my_fast_api.infrastructure.redis import RedisManager

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = init_db_engine(settings.database_url)
    await create_tables()

    _ = await RedisManager.connect(settings.redis_url)
    redis_client = await RedisManager.get_client()
    if not await redis_client.ping():
        raise RedisError("Redis is down")

    yield
    await RedisManager.disconnect()
    await engine.dispose()

limiter = get_limiter()

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(router)


class HealthCheckResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthCheckResponse)
@limiter.limit("5/minute")
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="up")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
