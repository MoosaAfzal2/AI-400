# Async Testing - pytest-asyncio Guide

Comprehensive guide for testing async FastAPI code with pytest-asyncio, covering fixtures, markers, event loops, and common patterns.

**Cross-Skill References**: See **fastapi-builder skill** for async endpoint patterns; see **async-sqlmodel skill** for async database design; see **pytest-testing skill** `fastapi-sqlmodel-testing.md` for database-specific async testing.

## Why Async Testing?

FastAPI is built on Starlette (async framework). To test FastAPI properly, you must:
- Test async endpoint handlers
- Test async database operations
- Test async external service calls
- Manage event loops correctly

Without pytest-asyncio, `await` in tests will fail. With it, pytest handles the event loop automatically.

---

## Setup

### Installation

```bash
pip install pytest-asyncio
```

### Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"          # Auto-detect async fixtures (recommended)
```

Or (pytest.ini):
```ini
[pytest]
asyncio_mode = auto
```

### What asyncio_mode Does

- **auto**: pytest detects async fixtures and test functions automatically
- **strict**: Requires @pytest.mark.asyncio on all async tests (explicit)

**Recommendation**: Use `auto` for modern projects.

---

## Async Test Functions

### Basic Async Test

```python
import pytest
from src.utils import fetch_user

@pytest.mark.asyncio
async def test_fetch_user():
    """Test async function"""
    user = await fetch_user(user_id=1)
    assert user.id == 1
    assert user.email == "user@example.com"
```

### Testing Async Context Managers

```python
from src.services import DatabaseConnection

@pytest.mark.asyncio
async def test_database_context_manager():
    """Test async context manager"""
    async with DatabaseConnection() as db:
        result = await db.query("SELECT 1")
        assert result == 1
```

### Testing FastAPI Endpoints (Async)

```python
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_get_user_endpoint():
    """Test FastAPI endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/users/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1
```

---

## Async Fixtures

### Basic Async Fixture

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

@pytest_asyncio.fixture
async def async_session():
    """Create async database session for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
```

### Async Fixture Scope

```python
# Function scope (default, fastest, isolated)
@pytest_asyncio.fixture
async def test_user(async_session):
    """Create test user (recreated per test)"""
    user = User(email="test@example.com")
    async_session.add(user)
    await async_session.commit()
    return user

# Module scope (shared across tests in file)
@pytest_asyncio.fixture(scope="module")
async def test_database(async_session):
    """Setup database once per module"""
    await seed_test_data(async_session)
    yield async_session
    # Cleanup here

# Session scope (shared across all tests)
@pytest_asyncio.fixture(scope="session")
async def event_loop():
    """Create event loop for all tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### Async Fixture Dependency

```python
@pytest_asyncio.fixture
async def test_user(async_session):
    """Create test user"""
    user = User(email="test@example.com")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def user_token(test_user):
    """Generate token for test user (depends on test_user)"""
    from src.core.security import create_access_token
    return create_access_token(str(test_user.id))

@pytest.mark.asyncio
async def test_endpoint_with_auth(async_client, user_token):
    """Use both fixtures together"""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
```

---

## Mixing Sync and Async

### Async Test with Sync Fixture

```python
@pytest.fixture
def sync_config():
    """Sync fixture can be used in async tests"""
    return {"debug": True, "timeout": 5}

@pytest.mark.asyncio
async def test_with_sync_fixture(sync_config):
    """Async test uses sync fixture"""
    assert sync_config["debug"] is True
    # Can still use await here
    result = await some_async_function()
    assert result is not None
```

### Sync Test with Async Fixture

```python
@pytest_asyncio.fixture
async def async_config():
    """Async fixture"""
    config = await load_config_async()
    return config

# ❌ Won't work - sync test can't use async fixture
# def test_sync_function(async_config):  # ERROR
#     pass

# ✅ Must be async to use async fixture
@pytest.mark.asyncio
async def test_with_async_fixture(async_config):
    """Async test uses async fixture"""
    assert async_config is not None
```

---

## Common Async Patterns

### Testing Async Database Operations

```python
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_user(async_session):
    """Test async user creation"""
    from src.models import User

    user = User(email="new@example.com", username="newuser")
    async_session.add(user)
    await async_session.commit()

    # Verify created
    result = await async_session.execute(
        select(User).where(User.email == "new@example.com")
    )
    created_user = result.scalar_one()
    assert created_user.email == "new@example.com"
```

### Testing Async HTTP Calls

```python
import httpx
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_external_api_call():
    """Test function that calls external API"""
    from src.services import ExternalService

    # Mock the HTTP call
    with unittest.mock.patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=AsyncMock(return_value={"id": 1, "name": "Test"})
        )

        service = ExternalService()
        result = await service.fetch_data()
        assert result["name"] == "Test"
```

### Testing Async Errors

```python
@pytest.mark.asyncio
async def test_async_error_handling():
    """Test error handling in async function"""
    from src.services import UserService

    service = UserService()

    with pytest.raises(ValueError, match="User not found"):
        await service.get_user(user_id=999)
```

### Testing Async Generators

```python
@pytest.mark.asyncio
async def test_async_generator():
    """Test async generator function"""
    from src.utils import stream_users

    users = []
    async for user in stream_users():
        users.append(user)
        if len(users) >= 3:
            break

    assert len(users) == 3
```

---

## Event Loop Management

### Auto Event Loop (Recommended)

```python
# With asyncio_mode = "auto", pytest-asyncio handles this:

@pytest.mark.asyncio
async def test_one():
    await some_async_operation()

@pytest.mark.asyncio
async def test_two():
    await another_async_operation()

# Each test gets its own event loop automatically
```

### Manual Event Loop (If Needed)

```python
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_with_manual_loop():
    """Uses the session event loop"""
    await some_async_function()
```

---

## FastAPI Testing Helpers

### AsyncClient (for async tests)

```python
import httpx
from src.main import app

@pytest.fixture
async def async_client():
    """Create async HTTP client for FastAPI"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_endpoint(async_client):
    """Test FastAPI endpoint asynchronously"""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
```

### TestClient (for sync tests)

```python
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def test_client():
    """Create sync HTTP client for FastAPI"""
    return TestClient(app)

def test_endpoint_sync(test_client):
    """Test FastAPI endpoint synchronously"""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
```

### Dependency Override (for both)

```python
from src.database import get_session

@pytest_asyncio.fixture
async def override_db_dependency(async_session):
    """Override FastAPI dependency for testing"""
    def get_session_override():
        return async_session

    app.dependency_overrides[get_session] = get_session_override
    yield
    del app.dependency_overrides[get_session]

@pytest.mark.asyncio
async def test_endpoint_with_override(async_client, override_db_dependency):
    """Test with overridden dependency"""
    response = await async_client.get("/api/v1/users")
    assert response.status_code == 200
```

---

## Debugging Async Tests

### Show Print Output

```bash
pytest -s test_async.py          # Show print statements
```

### Drop into Debugger

```bash
pytest --pdb test_async.py       # Enter pdb on failure
```

### Verbose Output

```bash
pytest -v -s test_async.py
```

### Trace Execution

```python
@pytest.mark.asyncio
async def test_with_debug():
    """Debug async execution"""
    import asyncio

    print("Starting test")

    result = await some_async_function()

    print(f"Result: {result}")
    assert result is not None
```

---

## Best Practices

✅ **Do:**
- Use `asyncio_mode = "auto"` in modern projects
- Use `@pytest_asyncio.fixture` for async fixtures
- Use `@pytest.mark.asyncio` only on test functions (fixtures auto-detected)
- Clean up resources in fixture teardown (after yield)
- Use in-memory SQLite for fast tests
- Mock external async services

❌ **Don't:**
- Mix sync and async without understanding implications
- Create multiple event loops unnecessarily
- Leave unclosed connections in tests
- Forget to await async operations
- Use sync fixtures with async operations

---

## Common Errors & Solutions

### Error: "RuntimeError: Event loop is closed"

```python
# ❌ Problem: Event loop closed before test completes
@pytest.mark.asyncio
async def test_something():
    loop = asyncio.get_event_loop()
    # Loop might be closed by pytest-asyncio

# ✅ Solution: Let pytest-asyncio manage the loop
@pytest.mark.asyncio
async def test_something():
    await some_async_operation()  # Don't manage loop manually
```

### Error: "no running event loop"

```python
# ❌ Problem: Using sync fixture's result in async context
@pytest.fixture
def sync_session():
    engine = create_engine("sqlite:///:memory:")
    return SessionLocal()

@pytest.mark.asyncio
async def test_async(sync_session):
    await sync_session.execute("SELECT 1")  # ERROR - sync session

# ✅ Solution: Use async session
@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    # ...
    yield session
```

---

## Summary

pytest-asyncio is essential for testing modern FastAPI applications. Key points:

1. **Setup**: `pip install pytest-asyncio`, set `asyncio_mode = auto`
2. **Fixtures**: Use `@pytest_asyncio.fixture` for async setup/teardown
3. **Tests**: Use `@pytest.mark.asyncio` on test functions with `await`
4. **Dependencies**: Async fixtures can depend on other async fixtures
5. **Event Loop**: Let pytest-asyncio manage (don't create manually)
6. **FastAPI**: Use AsyncClient for async tests, TestClient for sync tests
