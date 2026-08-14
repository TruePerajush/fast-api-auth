from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel
from redis import RedisError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import structlog
from structlog.stdlib import BoundLogger

from my_fast_api.common.logging import setup_logging
from my_fast_api.common.middleware import LoggingMiddleware
from my_fast_api.config import get_settings
from my_fast_api.dependencies import get_limiter
from my_fast_api.features.router import router
from my_fast_api.infrastructure.database import create_tables, init_db_engine
from my_fast_api.infrastructure.redis import RedisManager

setup_logging()
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


app = FastAPI(lifespan=lifespan)

limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(LoggingMiddleware)

app.include_router(router)


class HealthCheckResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthCheckResponse)
@limiter.limit("5/minute")
async def health_check(request: Request) -> HealthCheckResponse:
    logger: BoundLogger = structlog.get_logger()
    logger.info("health requested")
    return HealthCheckResponse(status="up")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
