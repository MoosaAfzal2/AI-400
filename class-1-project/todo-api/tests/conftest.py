"""Pytest configuration and fixtures."""

import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.todo_api.config import settings
from src.todo_api.database import get_session
from src.todo_api.models import Base, Todo, User
from src.todo_api.security import hash_password


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def engine():
    """Create test database engine (function-scoped for test isolation)."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Create test user (function-scoped for test isolation)."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPass123!"),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def test_user_id(test_user: User) -> int:
    """Get test user ID."""
    return test_user.id


@pytest.fixture
async def other_user(session: AsyncSession) -> User:
    """Create another test user for isolation testing."""
    user = User(
        email="other@example.com",
        password_hash=hash_password("OtherPass123!"),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def other_user_id(other_user: User) -> int:
    """Get other user ID."""
    return other_user.id


@pytest.fixture
async def test_user_data():
    """Test user registration data."""
    return {
        "email": "newuser@example.com",
        "password": "SecurePass123!",
    }


@pytest.fixture
async def auth_headers(test_user: User) -> dict:
    """Create authorization headers for test user."""
    from src.todo_api.security import create_access_token

    access_token = create_access_token(
        {
            "sub": test_user.id,
            "email": test_user.email,
            "type": "access",
        }
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def sample_todo(session: AsyncSession, test_user: User) -> Todo:
    """Create sample todo for test user."""
    todo = Todo(
        user_id=test_user.id,
        title="Sample Todo",
        description="This is a sample todo for testing",
        is_completed=False,
    )
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    return todo


@pytest.fixture
async def sample_todos(session: AsyncSession, test_user: User) -> list[Todo]:
    """Create multiple sample todos for test user."""
    todos = []
    for i in range(5):
        todo = Todo(
            user_id=test_user.id,
            title=f"Sample Todo {i+1}",
            description=f"Description for todo {i+1}",
            is_completed=i % 2 == 0,
        )
        session.add(todo)
        todos.append(todo)
    await session.commit()
    for todo in todos:
        await session.refresh(todo)
    return todos
