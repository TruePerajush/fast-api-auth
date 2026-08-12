import asyncio
from typing import AsyncGenerator, Generator

from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from httpx import ASGITransport, AsyncClient

import pytest

from my_fast_api.domain.entities import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory"

engine = create_async_engine(
    TEST_DB_URL,
    connect_agrs={"check_same_thread": False},
    poolclass=StaticPool,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_maker() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient]:
    async def override_get_db():
        yield db_session

    from my_fast_api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
