# Async Database Patterns - Production-Grade Setup

This guide covers production patterns for async database setup, connection pooling, and SQLModel ORM patterns based on real-world auth-service implementation.

## Connection Pooling Configuration

### Why Connection Pooling?

Database connections are expensive (3-5x TCP overhead). Pooling reuses connections efficiently:

- **Without pooling**: 100 requests = 100 new connections (slow, resource-intensive)
- **With pooling**: 100 requests = 10-15 connections reused (fast, efficient)

### Production Pool Configuration

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
import re

# Convert standard PostgreSQL URL to async version
database_url = "postgresql://user:password@localhost/dbname"
async_database_url = re.sub(
    r'^postgresql:',
    'postgresql+asyncpg:',
    database_url
)

# Production-grade async engine
engine = create_async_engine(
    async_database_url,

    # Echo SQL in development only
    echo=False,  # Set True only in development
    future=True,

    # Connection Pool Settings
    pool_size=10,                   # Base pool size (10 persistent connections)
    max_overflow=5,                 # 5 additional connections if needed (15 max total)
    pool_recycle=3600,              # Recycle connections every 1 hour
    pool_pre_ping=True,             # Verify connections before use

    # Connection-specific settings
    connect_args={
        "server_settings": {
            "application_name": "auth_service",  # Identify in DB logs
            "jit": "off",                       # Disable JIT for stable performance
        },
        "timeout": 10,                          # Connection timeout
    }
)

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects accessible after commit
    autoflush=False,         # Manual control over flush
    autocommit=False,        # Require explicit commit
)

async def get_session():
    """Dependency to provide database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
```

### Pool Settings Explained

| Setting | Value | Why |
|---------|-------|-----|
| `pool_size` | 10 | Base connections kept open |
| `max_overflow` | 5 | Temporary connections if needed (15 max) |
| `pool_recycle` | 3600 | Recycle after 1 hour (prevent stale PostgreSQL connections) |
| `pool_pre_ping` | True | Test connection before use (handles timeouts) |
| `expire_on_commit` | False | Keep objects in memory after commit |

---

## Database Initialization and Migrations

### Async Context Manager for Safe Operations

```python
async def init_db():
    """Initialize database (create tables)"""
    try:
        async with engine.begin() as conn:
            # Create all tables from models
            await conn.run_sync(Base.metadata.create_all)
        print("✓ Database tables created successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        raise

async def drop_db():
    """Drop all tables (development only)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("✓ Database tables dropped")

# Call on application startup
@app.on_event("startup")
async def startup_event():
    await init_db()

# Or with lifespan context manager (FastAPI 0.93+)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("Application startup complete")
    yield
    # Shutdown
    await engine.dispose()
    print("Application shutdown complete")

app = FastAPI(lifespan=lifespan)
```

### Alembic Migrations (for production)

Setup Alembic for database schema versioning:

```bash
# Initialize migrations
alembic init alembic

# Create first migration (auto-detect changes)
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback to previous
alembic downgrade -1

# Show migration history
alembic history
```

---

## Query Patterns

### Basic CRUD Operations

```python
from sqlalchemy import select, delete, update

# CREATE
async def create_user(db: AsyncSession, user_data: dict):
    """Insert new user"""
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)  # Fetch ID from database
    return user

# READ (single)
async def get_user_by_id(db: AsyncSession, user_id: UUID):
    """Fetch user by ID"""
    user = await db.get(User, user_id)
    return user

# READ (by field)
async def get_user_by_email(db: AsyncSession, email: str):
    """Fetch user by email"""
    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    return result.scalar_one_or_none()  # None if not found

# READ (all with pagination)
async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    """List users with pagination"""
    statement = select(User).offset(skip).limit(limit)
    result = await db.execute(statement)
    return result.scalars().all()

# UPDATE
async def update_user(db: AsyncSession, user_id: UUID, update_data: dict):
    """Update user fields"""
    user = await db.get(User, user_id)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# DELETE
async def delete_user(db: AsyncSession, user_id: UUID):
    """Delete user"""
    user = await db.get(User, user_id)
    if user:
        await db.delete(user)
        await db.commit()
        return True
    return False
```

### Advanced Query Patterns

```python
from sqlalchemy import and_, or_, func

# Complex WHERE conditions
async def search_users(db: AsyncSession, email: str, role: str):
    """Search users with multiple conditions"""
    statement = select(User).where(
        and_(
            User.email.ilike(f"%{email}%"),  # Case-insensitive search
            User.role == role
        )
    )
    result = await db.execute(statement)
    return result.scalars().all()

# OR conditions
async def find_user(db: AsyncSession, email: str, username: str):
    """Find user by email OR username"""
    statement = select(User).where(
        or_(
            User.email == email,
            User.username == username
        )
    )
    result = await db.execute(statement)
    return result.scalar_one_or_none()

# COUNT
async def count_active_users(db: AsyncSession):
    """Count active users"""
    statement = select(func.count(User.id)).where(User.is_active == True)
    result = await db.execute(statement)
    return result.scalar()

# Relationships (eager load)
async def get_user_with_tokens(db: AsyncSession, user_id: UUID):
    """Load user with related refresh tokens"""
    from sqlalchemy.orm import selectinload
    statement = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.refresh_tokens))
    )
    result = await db.execute(statement)
    return result.scalar_one_or_none()

# Bulk delete
async def delete_expired_tokens(db: AsyncSession, now: datetime):
    """Delete all expired refresh tokens"""
    statement = delete(RefreshToken).where(RefreshToken.expires_at < now)
    result = await db.execute(statement)
    await db.commit()
    return result.rowcount  # Number of deleted rows
```

### Transaction Management

```python
# Implicit transaction (each commit is a transaction)
async def create_user_with_token(db: AsyncSession, user_data: dict):
    """Create user and token in transaction"""
    try:
        # Create user
        user = User(**user_data)
        db.add(user)
        await db.flush()  # Insert but don't commit yet

        # Create token (if user creation fails, token won't be created)
        token = RefreshToken(user_id=user.id, token="...")
        db.add(token)

        # Both succeed or both fail
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        await db.rollback()
        raise

# Explicit transaction (more control)
async def transfer_data(db: AsyncSession):
    """Complex multi-step transaction"""
    async with db.begin():
        # Any error here triggers automatic rollback
        await db.execute(update(User).where(...).values(...))
        await db.execute(delete(RefreshToken).where(...))
        # All changes committed atomically on exit
```

---

## Error Handling

### Database Errors

```python
from sqlalchemy.exc import IntegrityError, NoResultFound, MultipleResultsFound

async def create_user_safe(db: AsyncSession, user_data: dict):
    """Create user with error handling"""
    try:
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError as e:
        await db.rollback()
        # Email or username already exists
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

# Specific query error handling
async def get_user_strict(db: AsyncSession, user_id: UUID):
    """Fetch user, raise error if not found"""
    try:
        statement = select(User).where(User.id == user_id)
        result = await db.execute(statement)
        return result.scalar_one()  # Raises if not found
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
```

---

## Performance Optimization

### Indexing Strategy

```python
from sqlalchemy import Index

class User(SQLModel, table=True):
    # Single-column indexes (fast equality checks)
    email: str = Field(unique=True, index=True)      # Lookup by email
    username: str = Field(unique=True, index=True)   # Lookup by username

class RefreshToken(SQLModel, table=True):
    token: str = Field(unique=True, index=True)      # Whitelist check
    user_id: UUID = Field(foreign_key="users.id", index=True)  # User lookup

    # Composite index for range queries
    __table_args__ = (
        Index('ix_refresh_token_user_expires', 'user_id', 'expires_at'),
    )
```

### Query Optimization

```python
# ❌ N+1 query problem (bad)
users = await db.execute(select(User))
for user in users.scalars():
    # This fetches tokens for each user (N+1)
    tokens = user.refresh_tokens

# ✅ Eager load relationships
from sqlalchemy.orm import selectinload
statement = (
    select(User)
    .options(selectinload(User.refresh_tokens))
)
result = await db.execute(statement)
users = result.unique().scalars()

# ✅ Pagination (limit result set)
statement = select(User).offset(0).limit(100)
result = await db.execute(statement)
users = result.scalars().all()
```

---

## Testing with Databases

### In-Memory SQLite for Tests

```python
import pytest
from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="function")
async def test_session():
    """Create in-memory database for tests"""
    # Use SQLite for testing (same schema, different backend)
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

# Usage in tests
@pytest.mark.asyncio
async def test_create_user(test_session):
    """Test user creation"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
    )
    test_session.add(user)
    await test_session.commit()

    # Verify
    result = await test_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    assert result.scalar() is not None
```

---

## Summary: Production Database Checklist

- ✅ Async SQLAlchemy with AsyncPG
- ✅ Connection pooling (10 base + 5 overflow)
- ✅ Pool recycling (1 hour)
- ✅ Pool pre-ping (health check)
- ✅ Proper indexes on frequently queried fields
- ✅ Cascade deletes for relationships
- ✅ Eager loading to prevent N+1 queries
- ✅ Pagination for large result sets
- ✅ Transaction management with rollback
- ✅ Error handling for IntegrityError, NoResultFound
- ✅ Migrations with Alembic
- ✅ Timezone-aware timestamps
- ✅ UUID primary keys
- ✅ In-memory SQLite for testing
