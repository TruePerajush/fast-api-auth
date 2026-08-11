from collections.abc import AsyncGenerator
from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine, create_async_engine

from my_fast_api.config import Settings
from my_fast_api.domain.entities import Base

# Singleton engine instance
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def init_db_engine(settings: Settings) -> AsyncEngine:
    global _engine, _session_maker
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        _session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )
    return _engine


async def get_db_engine() -> AsyncGenerator[AsyncEngine]:
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_db_engine() at startup.")
    yield _engine


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    if _session_maker is None:
        raise RuntimeError("Database session maker not initialized. Call init_db_engine() at startup.")
    async with _session_maker() as session:
        yield session

async def create_tables():
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_db_engine() first.")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
