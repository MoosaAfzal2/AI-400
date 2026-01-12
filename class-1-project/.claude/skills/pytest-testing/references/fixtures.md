# Pytest Fixtures - Complete Guide

Fixtures are reusable test setup/teardown functions. They provide objects, configuration, and data that tests need.

## Fixture Basics

### Simple Fixture

```python
import pytest

@pytest.fixture
def user_data():
    """Fixture returns test data"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePassword123!"
    }

def test_create_user(user_data):
    """Test uses fixture by parameter name"""
    assert user_data["email"] == "test@example.com"
```

### Fixture Cleanup (Teardown)

```python
@pytest.fixture
def temp_file():
    """Setup/teardown file"""
    file_path = "/tmp/test_file.txt"

    # Setup
    with open(file_path, "w") as f:
        f.write("test data")

    yield file_path  # Test runs here

    # Teardown
    import os
    os.remove(file_path)

def test_file_operations(temp_file):
    """File is created before test, deleted after"""
    with open(temp_file, "r") as f:
        content = f.read()
    assert content == "test data"
```

---

## Fixture Scope

Control how long fixture setup persists:

### Function Scope (Default)

```python
@pytest.fixture(scope="function")
async def test_user(async_session):
    """Created fresh for each test"""
    user = User(email="test@example.com")
    async_session.add(user)
    await async_session.commit()
    yield user
    # Cleaned up after each test

# Each test gets a new user
def test_one(test_user):
    assert test_user.email == "test@example.com"

def test_two(test_user):
    assert test_user.email == "test@example.com"  # Different instance
```

### Module Scope

```python
@pytest.fixture(scope="module")
async def shared_database(async_session):
    """Created once per file, shared across tests"""
    await seed_database(async_session)
    yield async_session
    # Cleaned up after all tests in module

def test_one(shared_database):
    pass

def test_two(shared_database):
    pass  # Same database as test_one
```

### Session Scope

```python
@pytest.fixture(scope="session")
def event_loop():
    """Created once for entire test run"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()  # Cleaned up after all tests
```

### Class Scope

```python
@pytest.fixture(scope="class")
def database():
    """Shared across all tests in a class"""
    db = Database()
    yield db

class TestUserOperations:
    def test_create(self, database):
        database.create_user(...)

    def test_update(self, database):
        database.update_user(...)  # Same database
```

---

## Fixture Dependencies

Fixtures can depend on other fixtures:

```python
@pytest.fixture
async def async_session():
    """Base async session"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    async with async_session() as session:
        yield session

@pytest.fixture
async def test_user(async_session):
    """Depends on async_session"""
    user = User(email="test@example.com")
    async_session.add(user)
    await async_session.commit()
    return user

@pytest.fixture
async def user_token(test_user):
    """Depends on test_user"""
    from src.core.security import create_access_token
    return create_access_token(str(test_user.id))

@pytest.mark.asyncio
async def test_auth_endpoint(async_client, user_token):
    """Uses user_token, which depends on test_user, which depends on async_session"""
    response = await async_client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
```

---

## Parametrized Fixtures

```python
@pytest.fixture(params=["user@example.com", "admin@example.com", "guest@example.com"])
def user_email(request):
    """Fixture returns different value for each test run"""
    return request.param

def test_email_validation(user_email):
    """Runs 3 times, once with each email"""
    assert "@" in user_email

# Alternative: parametrize with ids
@pytest.fixture(params=[
    ("user@example.com", "User"),
    ("admin@example.com", "Admin"),
    ("guest@example.com", "Guest"),
], ids=["user", "admin", "guest"])
def user_data(request):
    email, role = request.param
    return {"email": email, "role": role}

def test_user_role(user_data):
    """Runs 3 times with different data"""
    assert user_data["role"] in ["User", "Admin", "Guest"]
```

---

## Dynamic Fixtures (Using request)

```python
@pytest.fixture
def api_client(request):
    """Fixture accesses test metadata"""
    print(f"Test: {request.node.name}")

    client = APIClient()

    # Cleanup
    yield client
    client.close()

def test_api_call(api_client):
    """Prints: Test: test_api_call"""
    pass
```

---

## Fixture Example: Database

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import async_sessionmaker

@pytest_asyncio.fixture
async def test_database():
    """Complete database fixture for testing"""
    # Setup
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    # Teardown - drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.mark.asyncio
async def test_user_creation(test_database):
    """Database is created, used, then cleaned up"""
    user = User(email="test@example.com")
    test_database.add(user)
    await test_database.commit()
    assert user.id is not None
```

---

## Fixture Example: Authentication

```python
from src.core.security import create_access_token, hash_password
from uuid import uuid4

@pytest_asyncio.fixture
async def test_user(test_database):
    """Create test user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("TestPassword123!"),
        is_active=True,
    )
    test_database.add(user)
    await test_database.commit()
    await test_database.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Generate JWT headers for test user"""
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def authenticated_client(async_client, auth_headers):
    """HTTP client with authentication"""
    async_client.headers.update(auth_headers)
    return async_client

@pytest.mark.asyncio
async def test_protected_endpoint(authenticated_client):
    """Test uses pre-authenticated client"""
    response = await authenticated_client.get("/api/v1/me")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

---

## Fixture Example: FastAPI TestClient

```python
from fastapi.testclient import TestClient
import httpx

@pytest.fixture
def test_client():
    """Sync HTTP client for FastAPI"""
    from src.main import app
    return TestClient(app)

@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client for FastAPI"""
    from src.main import app
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

def test_sync_endpoint(test_client):
    """Use sync client"""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    """Use async client"""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
```

---

## Fixture Example: Mock Data

```python
@pytest.fixture
def user_create_payload():
    """Valid user creation payload"""
    return {
        "email": "new@example.com",
        "username": "newuser",
        "password": "SecurePassword123!",
    }

@pytest.fixture
def multiple_users(test_database):
    """Create multiple test users"""
    users = []
    for i in range(5):
        user = User(
            email=f"user{i}@example.com",
            username=f"user{i}",
        )
        test_database.add(user)
        users.append(user)
    test_database.commit()
    return users

def test_user_creation(test_client, user_create_payload):
    """Create new user"""
    response = test_client.post("/api/v1/users", json=user_create_payload)
    assert response.status_code == 201

def test_list_users(test_client, multiple_users):
    """List multiple users"""
    response = test_client.get("/api/v1/users")
    assert len(response.json()) == 5
```

---

## Best Practices

✅ **Do:**
- Use fixtures for common setup/teardown
- Keep fixtures focused and single-purpose
- Name fixtures descriptively
- Use appropriate scope (function is usually best)
- Document fixture purpose
- Organize fixtures in conftest.py
- Use parametrization for multiple variations
- Clean up resources in teardown (after yield)

❌ **Don't:**
- Create fixtures with side effects
- Make fixtures depend on too many other fixtures
- Use session-scoped fixtures for mutable state
- Forget to yield (or return) from fixture
- Create state that persists between tests
- Use global variables instead of fixtures
