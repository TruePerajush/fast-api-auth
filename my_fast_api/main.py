from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from redis import RedisError

from my_fast_api.config import get_settings
from my_fast_api.features.router import router
from my_fast_api.infrastructure.database import create_tables, init_db_engine
from my_fast_api.infrastructure.redis import RedisManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    engine = init_db_engine(settings.database_url)
    await create_tables()

    await RedisManager.connect(settings.redis_url)
    redis_client = await RedisManager.get_client()
    if not await redis_client.ping():
            raise RedisError("Redis is down")

    yield
    await RedisManager.disconnect()
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
