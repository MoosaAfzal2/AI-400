"""Database configuration and session management."""

from typing import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from .config import settings

logger = logging.getLogger(__name__)

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
# Wrap in try-except to handle missing database drivers in development
try:
    engine: AsyncEngine = create_async_engine(
        settings.DATABASE_URL,
        **_engine_kwargs,
    )
except ModuleNotFoundError as e:
    logger.warning(f"Database driver not available: {e}. Running in development mode without database.")
    engine = None

# Create async session factory only if engine exists
if engine:
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
else:
    AsyncSessionLocal = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.

    Yields:
        AsyncSession: Database session for request.

    Raises:
        RuntimeError: If database is not available.
    """
    if not engine or not AsyncSessionLocal:
        raise RuntimeError("Database is not available. Check DATABASE_URL and database driver installation.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables (create if not exist)."""
    if not engine:
        logger.info("Skipping database initialization - database not available in development mode.")
        return

    try:
        from .models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
    except Exception as exc:
        logger.error(f"Failed to initialize database: {exc}")
        # Don't raise - allow the app to start anyway


async def close_db() -> None:
    """Close database connection."""
    if engine:
        await engine.dispose()
