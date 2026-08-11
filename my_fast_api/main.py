from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from my_fast_api.features.router import router
from my_fast_api.infrastructure.database import create_tables, engine
from my_fast_api.infrastructure.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    print("created")
    if not await redis_client.ping():
        raise Exception("Redis is down")
    yield
    await engine.dispose()
    await redis_client.aclose()


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
