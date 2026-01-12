# Async Database Setup - SQLModel Patterns

Configure async database connections with SQLModel and SQLAlchemy. This guide covers engine creation, connection pooling, async sessions, and FastAPI integration.

## Async Engine Creation

### Basic Async Engine Setup

```python
# src/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlmodel import SQLModel

# ============================================================================
# ASYNC ENGINE - Production Ready
# ============================================================================

# PostgreSQL with asyncpg (recommended for production)
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/dbname"

# SQLite with aiosqlite (development)
# DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    future=True,
)

# ============================================================================
# ASYNC SESSION FACTORY
# ============================================================================

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects accessible after commit
    autocommit=False,
    autoflush=False,
)

# ============================================================================
# DATABASE SETUP
# ============================================================================

async def init_db():
    """Create all tables (development only)"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def close_db():
    """Close database connection (on shutdown)"""
    await engine.dispose()
```

---

## Connection Pooling Configuration

### Production Connection Pool

```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

# PostgreSQL with production pooling
engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost:5432/dbname",
    # Connection pooling
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,              # Number of connections to maintain
    max_overflow=0,            # Don't create extra connections beyond pool_size
    pool_pre_ping=True,        # Test connections before using (detect stale connections)
    pool_recycle=3600,         # Recycle connections after 1 hour

    # Echo for debugging
    echo=False,

    # Engine options
    connect_args={
        "timeout": 30,         # Connection timeout in seconds
        "server_settings": {
            "application_name": "myapp",
        },
    },
)
```

### Development SQLite (No Pooling)

```python
# SQLite doesn't support concurrent connections
# Use NullPool for development
engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    echo=True,  # Show SQL queries
    poolclass=NullPool,  # No connection pooling for SQLite
    connect_args={"check_same_thread": False},
)
```

---

## AsyncSession Configuration

### Session Lifecycle

```python
from sqlalchemy.ext.asyncio import AsyncSession

# Configure async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Keep objects after commit
    autocommit=False,          # Don't auto-commit (manual commit)
    autoflush=False,           # Don't auto-flush (manual flush)
)

# ============================================================================
# USING SESSION
# ============================================================================

async def get_session() -> AsyncSession:
    """Get a new async session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# Example: Using session directly
async def create_user(username: str) -> None:
    """Create user and commit"""
    async with async_session_maker() as session:
        # Create
        user = User(username=username)
        session.add(user)

        # Flush to get ID
        await session.flush()

        # Commit
        await session.commit()

        # Refresh to reload from DB
        await session.refresh(user)

        print(f"Created user: {user.id} - {user.username}")
```

---

## FastAPI Integration

### Session as Dependency

```python
# src/database.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_session() -> AsyncSession:
    """Provide AsyncSession for FastAPI endpoints"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ============================================================================
# USE IN ENDPOINTS
# ============================================================================

# src/api/users.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.models import User

router = APIRouter()

@router.post("/users/")
async def create_user(
    username: str,
    session: AsyncSession = Depends(get_session)
):
    """Create user using injected session"""
    user = User(username=username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get user from database"""
    user = await session.get(User, user_id)
    return user
```

### Lifespan Setup/Teardown

```python
# src/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting up...")
    await init_db()

    yield

    # Shutdown
    print("🛑 Shutting down...")
    await close_db()

app = FastAPI(lifespan=lifespan)

# Now database is initialized on startup and closed on shutdown
```

---

## Testing with Async Database

### Test Database Setup

```python
# tests/conftest.py

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

@pytest_asyncio.fixture
async def test_engine():
    """Create in-memory test database"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()

@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test session"""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

@pytest.fixture
def override_get_session(test_session):
    """Override FastAPI dependency with test session"""
    from src.database import get_session
    from src.main import app

    async def get_session_override():
        return test_session

    app.dependency_overrides[get_session] = get_session_override
    yield
    del app.dependency_overrides[get_session]
```

---

## Connection Pooling Best Practices

### Pool Configuration by Database

```python
# PostgreSQL - High concurrency
engine = create_async_engine(
    DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# MySQL - High concurrency
engine = create_async_engine(
    "mysql+aiomysql://user:password@localhost:3306/dbname",
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# SQLite - No pooling (single file)
engine = create_async_engine(
    "sqlite+aiosqlite:///./app.db",
    poolclass=NullPool,
    connect_args={"check_same_thread": False},
)
```

### Connection Pool Sizing

```
Pool Size Rules of Thumb:

Light Load (< 100 requests/sec):
├─ pool_size = 5
├─ max_overflow = 5

Medium Load (100-1000 requests/sec):
├─ pool_size = 10-20
├─ max_overflow = 10

Heavy Load (1000+ requests/sec):
├─ pool_size = 20-30
├─ max_overflow = 0 (let requests queue)
└─ Consider connection pooling proxy (PgBouncer)
```

---

## Error Handling

### Connection Errors

```python
from sqlalchemy.exc import SQLAlchemyError

async def get_session() -> AsyncSession:
    """Provide session with error handling"""
    async with async_session_maker() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise Exception(f"Database error: {str(e)}")
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Stale Connection Detection

```python
# Enable pool_pre_ping to detect stale connections
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connection before each use
    echo=False,
)

# This runs a simple SELECT 1 before using connection
# Detects and removes stale connections from pool
```

---

## Monitoring Connection Pool

### Log Pool Status

```python
# src/monitoring.py

from sqlalchemy.pool import Pool

def log_pool_status(dbapi_conn, connection_record):
    """Log pool status on connect"""
    pool = dbapi_conn.connection_record.connection.pool
    print(f"Pool size: {pool.size()}")
    print(f"Pool checked out: {pool.checkedout()}")

engine.pool.connect = log_pool_status
```

### Production Monitoring

```python
# Monitor pool metrics
def get_pool_metrics():
    """Get current pool metrics"""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "connections": pool.size(),
    }
```

---

## Environment Configuration

### Using Environment Variables

```python
# src/config.py

import os
from typing import Optional

class Settings:
    """Database configuration from environment"""

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./test.db"
    )

    POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    POOL_PRE_PING: bool = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
    POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))

    # Development vs Production
    ECHO_SQL: bool = os.getenv("DB_ECHO", "false").lower() == "true"

settings = Settings()

# Use in engine creation
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ECHO_SQL,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_pre_ping=settings.POOL_PRE_PING,
    pool_recycle=settings.POOL_RECYCLE,
)
```

### Example .env File

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/myapp
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=3600
DB_ECHO=false
```

---

## Database Setup Checklist

Before using in production:

- [ ] Async engine created with correct driver (asyncpg, aiosqlite, aiomysql)
- [ ] AsyncSession configured with expire_on_commit=False
- [ ] Connection pooling configured (pool_size, max_overflow, pool_pre_ping)
- [ ] Session dependency created for FastAPI endpoints
- [ ] Error handling with rollback on exceptions
- [ ] Lifespan setup for init_db() and close_db()
- [ ] Environment variables for configuration
- [ ] Test database setup with in-memory SQLite
- [ ] Connection string correct for target database
- [ ] Pool parameters tuned for expected load

---

## Summary

Async database setup requires:
1. **Async engine** with correct driver (asyncpg for PostgreSQL)
2. **AsyncSession** factory with expire_on_commit=False
3. **Connection pooling** configured for production (pool_pre_ping, pool_size)
4. **FastAPI dependency** for session injection
5. **Lifespan events** for startup/shutdown
6. **Error handling** with rollback on exceptions
