"""Async database engine and session factory."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings


def create_engine(settings: Settings | None = None) -> AsyncEngine:
    """Create an async SQLAlchemy engine from settings."""
    resolved = settings or get_settings()
    return create_async_engine(
        resolved.database_url,
        pool_size=resolved.db_pool_size,
        max_overflow=resolved.db_max_overflow,
        pool_pre_ping=True,
    )


engine = create_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield one async database session for a request."""
    async with AsyncSessionLocal() as session:
        yield session
