"""Database configuration and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from .config import settings

# Build engine kwargs based on database type
_engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}

# Only add PostgreSQL-specific options for non-SQLite databases
if "sqlite" not in settings.DATABASE_URL.lower():
    _engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 0,
        "pool_pre_ping": True,
        "connect_args": {"server_settings": {"application_name": "todo-api"}},
    })
else:
    # SQLite specific settings
    _engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
    })

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    **_engine_kwargs,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.

    Yields:
        AsyncSession: Database session for request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables (create if not exist)."""
    from .models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connection."""
    await engine.dispose()
