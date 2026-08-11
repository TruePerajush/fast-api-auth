from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from my_fast_api.dependencies import get_settings


async def get_db_engine():
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True
    )
    try:
        yield engine
    finally:
        await engine.dispose()

async def get_db_session(
    engine_provider=Depends(get_db_engine)
) -> AsyncGenerator[AsyncSession]:
    async_session_maker = async_sessionmaker(
        engine_provider,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session
