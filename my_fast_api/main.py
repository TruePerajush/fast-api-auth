from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from redis.exceptions import RedisError

from my_fast_api.config import get_settings
from my_fast_api.features.router import router
from my_fast_api.infrastructure.database import create_tables, init_db_engine
from my_fast_api.infrastructure.redis import get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = init_db_engine(get_settings())
    await create_tables()

    redis_client = await get_redis()
    if not await redis_client.ping():
        raise RedisError("Redis is down")
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


class HealthCheckResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="ok")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
