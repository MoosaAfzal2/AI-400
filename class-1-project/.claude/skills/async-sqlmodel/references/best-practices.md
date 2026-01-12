# SQLModel Best Practices - Production Patterns

Professional patterns, architecture decisions, performance optimization, and reliability practices for async SQLModel applications.

## Model Organization

### File Structure

```
src/
├── models/
│   ├── __init__.py              # Export all models
│   ├── base.py                  # Base model with common fields
│   ├── user.py                  # User model
│   ├── team.py                  # Team model
│   ├── product.py               # Product model
│   └── schemas.py               # Response models (Pydantic only)
├── services/
│   ├── __init__.py
│   ├── user.py                  # User CRUD service
│   ├── team.py                  # Team CRUD service
│   └── product.py               # Product CRUD service
├── api/
│   ├── routes/
│   │   ├── users.py            # User endpoints
│   │   ├── teams.py            # Team endpoints
│   │   └── products.py         # Product endpoints
│   └── dependencies.py          # Shared dependencies
├── database.py                  # Database configuration
└── main.py                      # FastAPI app
```

### Base Model with Common Fields

```python
# src/models/base.py

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class BaseModel(SQLModel):
    """Base model with common fields"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel, table=True):
    """User inherits id, created_at, updated_at"""
    __tablename__ = "users"
    username: str
    email: str
```

---

## Service Layer Pattern

### Separation of Concerns

```python
# src/services/user.py

from sqlalchemy.ext.asyncio import AsyncSession
from src.models import User

class UserService:
    """Encapsulates user business logic"""

    @staticmethod
    async def create_user(
        session: AsyncSession,
        username: str,
        email: str,
    ) -> User:
        """Create user"""
        user = User(username=username, email=email)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_user(
        session: AsyncSession,
        user_id: int,
    ) -> Optional[User]:
        """Get user by ID"""
        return await session.get(User, user_id)

    @staticmethod
    async def get_users(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[User], int]:
        """Get paginated users"""
        # Count
        from sqlalchemy import func, select
        count_statement = select(func.count(User.id))
        count_result = await session.execute(count_statement)
        total = count_result.scalar()

        # Get paginated
        statement = select(User).offset(skip).limit(limit)
        result = await session.execute(statement)
        users = result.scalars().all()

        return users, total

# Use in endpoints
# src/api/routes/users.py

from src.services.user import UserService
from src.database import get_session

@router.get("/users/")
async def list_users(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
):
    users, total = await UserService.get_users(session, skip, limit)
    return {"items": users, "total": total}
```

---

## Connection Pooling

### Production Configuration

```python
# src/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncAdaptedQueuePool

engine = create_async_engine(
    DATABASE_URL,
    # Connection pooling
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,              # Maintain 20 connections
    max_overflow=10,           # Allow 10 extra temporary connections
    pool_pre_ping=True,        # Test connections before use (detect stale)
    pool_recycle=3600,         # Recycle connections after 1 hour

    # Performance
    echo=False,                # Disable SQL logging in production

    # Async options
    connect_args={
        "timeout": 30,         # Connection timeout
        "server_settings": {
            "application_name": "myapp",
        },
    },
)
```

### Pool Sizing by Load

```
Light Load (< 100 req/sec):
├─ pool_size = 5
├─ max_overflow = 5

Medium Load (100-1000 req/sec):
├─ pool_size = 10-20
├─ max_overflow = 10

Heavy Load (1000+ req/sec):
├─ pool_size = 20-30
├─ max_overflow = 0
└─ Consider connection pooling proxy (PgBouncer)
```

---

## Eager Loading Strategy

### Always Eager Load Before Access

```python
# ❌ BAD
async def get_teams(session):
    statement = select(Team)
    result = await session.execute(statement)
    teams = result.scalars().all()
    # Accessing .players causes N+1 queries
    for team in teams:
        print(team.players)

# ✅ GOOD
async def get_teams(session):
    from sqlalchemy.orm import selectinload
    statement = select(Team).options(selectinload(Team.players))
    result = await session.execute(statement)
    teams = result.scalars().all()
    # No additional queries
    for team in teams:
        print(team.players)
```

### Default Eager Loading in Services

```python
from sqlalchemy.orm import selectinload, joinedload

class TeamService:
    @staticmethod
    async def get_team_with_players(
        session: AsyncSession,
        team_id: int,
    ) -> Optional[Team]:
        """Get team with eagerly loaded players"""
        statement = (
            select(Team)
            .where(Team.id == team_id)
            .options(selectinload(Team.players))
        )
        result = await session.execute(statement)
        return result.unique().scalar_one_or_none()
```

---

## Testing Patterns

### Test with In-Memory Database

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

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

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
```

### Test Service Layer

```python
@pytest.mark.asyncio
async def test_create_user(test_session):
    """Test user creation"""
    from src.services.user import UserService

    user = await UserService.create_user(
        test_session,
        "john",
        "john@example.com",
    )
    assert user.id is not None
    assert user.username == "john"

@pytest.mark.asyncio
async def test_duplicate_user(test_session):
    """Test duplicate username error"""
    from src.services.user import UserService

    await UserService.create_user(test_session, "john", "john@example.com")

    with pytest.raises(IntegrityError):
        await UserService.create_user(test_session, "john", "john2@example.com")
```

---

## Error Handling

### Consistent Error Handling

```python
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

async def safe_operation(
    session: AsyncSession,
    operation_name: str,
    async_func,
):
    """Execute database operation with consistent error handling"""
    try:
        result = await async_func()
        await session.commit()
        return result
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate entry for {operation_name}",
        )
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during {operation_name}",
        )
    except Exception:
        await session.rollback()
        raise
```

---

## Migration Strategy

### Development vs Production

```bash
# Development: Create all tables on startup
await init_db()  # Creates all tables

# Production: Use Alembic migrations
alembic upgrade head
```

### Backup Before Major Migrations

```bash
# Create database backup
pg_dump myapp > backup.sql

# Test migration on backup first
# Then run on production:
alembic upgrade head
```

---

## Naming Conventions

### ✅ Good Naming

```python
# Models use singular noun
class User(SQLModel, table=True):
    __tablename__ = "users"  # Tables use plural

# Services use Noun + Service
class UserService:
    async def create_user(self, ...): pass

# Endpoints use plural nouns
@router.post("/users/")
async def create_user(...): pass

@router.get("/users/{user_id}")
async def get_user(...): pass

# Response models use Noun + Response/Public
class UserResponse(SQLModel):
    id: int
    username: str
```

### ❌ Avoid

```python
# ❌ Don't: Confusing names
class UserModel(SQLModel):  # "Model" is redundant

class UserCRUD:  # Too generic
    def do_user_stuff(self): pass  # Vague naming

@router.post("/create/")  # Redundant with POST
async def create_user(...): pass
```

---

## Documentation

### Docstrings

```python
class User(SQLModel, table=True):
    """User account in the system.

    Attributes:
        id: Unique identifier
        username: Unique username (3-50 chars)
        email: Unique email address
        is_active: Whether account is active
        created_at: Timestamp of account creation
    """
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(min_length=3, max_length=50)
    email: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## Security

### Never Expose Sensitive Data

```python
# ❌ Bad: Password in response model
class UserResponse(SQLModel):
    id: int
    username: str
    password: str  # NEVER!

# ✅ Good: Separate public response
class UserPublic(SQLModel):
    id: int
    username: str
    email: str
    # password excluded
```

### Validate Input

```python
from pydantic import field_validator

class UserCreate(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: str

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Username must be alphanumeric"""
        if not v.isalnum():
            raise ValueError("Must be alphanumeric")
        return v
```

---

## Performance Tips

### Use Indexes

```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)  # Index for searches
    email: str = Field(index=True, unique=True)    # Index for lookups
    created_at: datetime = Field(index=True)       # Index for date ranges
```

### Batch Operations

```python
# Insert multiple records efficiently
users = [User(username=f"user{i}") for i in range(1000)]
session.add_all(users)
await session.commit()
```

### Pagination Always

```python
# Don't fetch all records
# ❌ Bad
statement = select(User)

# ✅ Good
statement = select(User).offset(skip).limit(limit)
```

---

## Monitoring

### Log Database Operations

```python
import logging

logger = logging.getLogger(__name__)

async def create_user(session, username, email):
    logger.info(f"Creating user: {username}")
    user = User(username=username, email=email)
    session.add(user)
    await session.commit()
    logger.info(f"User created: {user.id}")
    return user
```

### Monitor Connection Pool

```python
def get_pool_status():
    """Get current pool metrics"""
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }
```

---

## Best Practices Checklist

Before production deployment:

- [ ] Models organized in separate files by domain
- [ ] Base model used for common fields (id, created_at, updated_at)
- [ ] Service layer encapsulates business logic
- [ ] All relationships are eagerly loaded
- [ ] Connection pooling configured for expected load
- [ ] Migrations managed with Alembic
- [ ] Error handling consistent across endpoints
- [ ] Sensitive data excluded from response models
- [ ] Input validation with Pydantic
- [ ] Tests use in-memory database
- [ ] Indexes created for frequently queried fields
- [ ] Pagination implemented on list endpoints
- [ ] Logging configured for debugging
- [ ] No N+1 query problems
- [ ] Documentation includes docstrings

---

## Summary

Production SQLModel applications require:
1. **Clear organization** with service layer pattern
2. **Proper connection pooling** for concurrency
3. **Eager loading** to avoid lazy loading issues
4. **Comprehensive error handling** with rollback
5. **Input validation** and security hardening
6. **Testing** with fixtures and mocking
7. **Monitoring** and logging
8. **Documentation** and type hints
