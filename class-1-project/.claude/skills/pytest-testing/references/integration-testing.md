# Integration Testing - FastAPI Patterns

Integration tests verify that multiple components work together correctly. They test with real or test databases, multiple services, and end-to-end request flows.

## Integration Testing Overview

### Unit vs Integration Tests

```
┌─────────────────────────────────────────────────┐
│              Test Pyramid                       │
├─────────────────────────────────────────────────┤
│        E2E Tests (Few, slow)                    │
│        Integration Tests (Medium, moderate)    │
│        Unit Tests (Many, fast)                  │
└─────────────────────────────────────────────────┘

Unit: Isolated functions (mock dependencies)
Integration: Real components working together
E2E: Complete request flows through API
```

### Integration Test Setup

```python
# tests/integration/test_user_endpoints.py

import pytest
from httpx import AsyncClient
from src.main import app
from src.models import User

@pytest.mark.integration
@pytest.mark.asyncio
class TestUserEndpoints:
    """Integration tests for user endpoints"""
```

---

## Database Integration Testing

### Testing with Real Test Database

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import async_sessionmaker

@pytest_asyncio.fixture
async def test_database():
    """Create test database"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
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

### Testing Database Operations

```python
@pytest.mark.asyncio
async def test_create_user_in_database(test_database):
    """User created in database can be retrieved"""
    from src.models import User
    from sqlalchemy import select

    # Create user
    user = User(
        email="test@example.com",
        username="testuser",
    )
    test_database.add(user)
    await test_database.commit()

    # Verify created
    result = await test_database.execute(
        select(User).where(User.email == "test@example.com")
    )
    created_user = result.scalar_one()

    assert created_user.email == "test@example.com"
    assert created_user.id is not None
```

### Testing Database Relationships

```python
@pytest.mark.asyncio
async def test_user_posts_relationship(test_database):
    """User can have multiple posts"""
    from src.models import User, Post
    from sqlalchemy import select

    # Create user with posts
    user = User(email="author@example.com", username="author")
    post1 = Post(title="Post 1", user=user)
    post2 = Post(title="Post 2", user=user)

    test_database.add(user)
    test_database.add(post1)
    test_database.add(post2)
    await test_database.commit()

    # Verify relationship
    result = await test_database.execute(
        select(User).where(User.email == "author@example.com")
    )
    retrieved_user = result.scalar_one()

    await test_database.refresh(retrieved_user, ["posts"])
    assert len(retrieved_user.posts) == 2
    assert retrieved_user.posts[0].title == "Post 1"
```

### Testing Database Constraints

```python
@pytest.mark.asyncio
async def test_duplicate_email_raises_error(test_database):
    """Database constraint prevents duplicate emails"""
    from src.models import User
    from sqlalchemy.exc import IntegrityError

    # Create first user
    user1 = User(email="test@example.com", username="user1")
    test_database.add(user1)
    await test_database.commit()

    # Try to create duplicate
    user2 = User(email="test@example.com", username="user2")
    test_database.add(user2)

    with pytest.raises(IntegrityError):
        await test_database.commit()
```

---

## FastAPI Endpoint Integration Testing

### Testing Endpoints with AsyncClient

```python
import httpx
import pytest

@pytest_asyncio.fixture
async def async_client():
    """Create async HTTP client for FastAPI"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_create_user_endpoint(async_client, test_database):
    """POST /users creates new user"""
    payload = {
        "email": "new@example.com",
        "username": "newuser",
        "password": "Password123!"
    }

    response = await async_client.post("/api/v1/users", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["id"] is not None
```

### Testing GET Endpoints

```python
@pytest.mark.asyncio
async def test_get_user_endpoint(async_client, test_user):
    """GET /users/{id} returns user"""
    response = await async_client.get(f"/api/v1/users/{test_user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id
```

### Testing List Endpoints with Pagination

```python
@pytest.mark.asyncio
async def test_list_users_pagination(async_client, multiple_users):
    """GET /users returns paginated list"""
    response = await async_client.get(
        "/api/v1/users",
        params={"skip": 0, "limit": 10}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == len(multiple_users)
    assert data["total"] == len(multiple_users)
```

### Testing UPDATE Endpoints

```python
@pytest.mark.asyncio
async def test_update_user_endpoint(async_client, test_user):
    """PUT /users/{id} updates user"""
    update_payload = {
        "email": "updated@example.com",
        "username": "updateduser"
    }

    response = await async_client.put(
        f"/api/v1/users/{test_user.id}",
        json=update_payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"
```

### Testing DELETE Endpoints

```python
@pytest.mark.asyncio
async def test_delete_user_endpoint(async_client, test_user):
    """DELETE /users/{id} removes user"""
    response = await async_client.delete(f"/api/v1/users/{test_user.id}")

    assert response.status_code == 204

    # Verify deleted
    response = await async_client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == 404
```

---

## Testing with Authentication

### Testing Protected Endpoints

```python
@pytest.fixture
def auth_headers(test_user):
    """Generate JWT headers for test user"""
    from src.core.security import create_access_token

    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(async_client):
    """Protected endpoint requires authentication"""
    response = await async_client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_protected_endpoint_with_auth(async_client, auth_headers):
    """Protected endpoint returns data with valid token"""
    response = await async_client.get(
        "/api/v1/me",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

### Testing Login Endpoint

```python
@pytest.mark.asyncio
async def test_login_success(async_client, test_user):
    """POST /login returns access token"""
    response = await async_client.post(
        "/api/v1/login",
        data={
            "username": test_user.username,
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_password(async_client, test_user):
    """POST /login with wrong password fails"""
    response = await async_client.post(
        "/api/v1/login",
        data={
            "username": test_user.username,
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
```

---

## Testing Error Responses

### Testing Validation Errors

```python
@pytest.mark.asyncio
async def test_create_user_validation_error(async_client):
    """POST /users with invalid data returns 422"""
    # Missing required field
    response = await async_client.post(
        "/api/v1/users",
        json={"username": "user"}  # Missing email
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("email" in str(d) for d in data["detail"])
```

### Testing Not Found Errors

```python
@pytest.mark.asyncio
async def test_get_nonexistent_user(async_client):
    """GET /users/{id} with invalid id returns 404"""
    response = await async_client.get("/api/v1/users/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
```

### Testing Server Errors

```python
@pytest.mark.asyncio
async def test_database_error_handling(async_client, mocker):
    """Database error returns 500 with safe message"""
    # Mock database to raise error
    mocker.patch(
        "src.services.UserService.get_user",
        side_effect=Exception("Database connection failed")
    )

    response = await async_client.get("/api/v1/users/1")

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]
```

---

## Testing Workflows (Multiple Steps)

### Testing Complete User Registration Flow

```python
@pytest.mark.asyncio
async def test_user_registration_workflow(async_client, test_database):
    """Complete registration flow: create, login, access profile"""
    # Step 1: Register new user
    register_response = await async_client.post(
        "/api/v1/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "Password123!"
        }
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]

    # Step 2: Login
    login_response = await async_client.post(
        "/api/v1/login",
        data={
            "username": "newuser",
            "password": "Password123!"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Step 3: Access protected profile
    profile_response = await async_client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["id"] == user_id
```

### Testing Order Processing Workflow

```python
@pytest.mark.asyncio
async def test_order_creation_workflow(async_client, test_user, auth_headers):
    """Complete order workflow: create, confirm, retrieve"""
    # Create order
    create_response = await async_client.post(
        "/api/v1/orders",
        json={
            "items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1}
            ]
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    order_id = create_response.json()["id"]

    # Confirm order
    confirm_response = await async_client.post(
        f"/api/v1/orders/{order_id}/confirm",
        headers=auth_headers
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "confirmed"

    # Retrieve order
    get_response = await async_client.get(
        f"/api/v1/orders/{order_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "confirmed"
```

---

## Testing with External Service Mocking

### Mocking External APIs

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_send_email_on_user_creation(async_client, mocker):
    """Sending email is called when user created"""
    # Mock email service
    mock_email = AsyncMock()
    mocker.patch(
        "src.services.send_email",
        mock_email
    )

    response = await async_client.post(
        "/api/v1/users",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "Password123!"
        }
    )

    assert response.status_code == 201
    mock_email.assert_called_once()
    call_args = mock_email.call_args
    assert "new@example.com" in call_args[0]
```

### Mocking External Payment API

```python
@pytest.mark.asyncio
async def test_payment_processing(async_client, test_user, auth_headers, mocker):
    """Payment endpoint processes charge correctly"""
    mock_payment = AsyncMock()
    mock_payment.return_value = {"transaction_id": "tx_123", "status": "success"}

    mocker.patch(
        "src.services.PaymentService.charge",
        mock_payment
    )

    response = await async_client.post(
        "/api/v1/payments",
        json={"amount": 99.99, "currency": "USD"},
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_payment.assert_called_once()
```

---

## Testing Response Formats

### Testing Response Schema

```python
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    email: str
    username: str

@pytest.mark.asyncio
async def test_user_response_schema(async_client, test_user):
    """GET /users/{id} returns correct schema"""
    response = await async_client.get(f"/api/v1/users/{test_user.id}")

    assert response.status_code == 200

    # Validate schema
    user_data = response.json()
    user = UserResponse(**user_data)

    assert user.email == test_user.email
    assert user.username == test_user.username
```

### Testing List Response Pagination

```python
@pytest.mark.asyncio
async def test_list_response_structure(async_client, multiple_users):
    """List endpoints return proper pagination structure"""
    response = await async_client.get("/api/v1/users?skip=0&limit=10")

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data

    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
```

---

## Integration Test Markers & Organization

### Using Markers to Categorize Tests

```python
# pytest.ini
[tool.pytest.ini_options]
markers = [
    "integration: integration tests",
    "db: tests requiring database",
    "async: async tests",
    "auth: authentication tests",
]

# Usage
@pytest.mark.integration
@pytest.mark.db
async def test_something():
    pass
```

### Running Specific Integration Tests

```bash
# Run all integration tests
pytest -m integration

# Run integration + database tests
pytest -m "integration and db"

# Skip slow tests
pytest -m "not slow"
```

---

## Integration Test Checklist

Before committing integration tests:

- [ ] Database setup/teardown is clean
- [ ] Tests are isolated (don't depend on execution order)
- [ ] External services are mocked (except test database)
- [ ] Authentication is tested (valid and invalid tokens)
- [ ] Response status codes are correct
- [ ] Response schemas are validated
- [ ] Error responses are tested
- [ ] Multi-step workflows are tested
- [ ] Database constraints are verified
- [ ] All fixtures are properly scoped
- [ ] Tests are marked appropriately (@pytest.mark.integration)
- [ ] Run with `pytest -m integration` works cleanly
