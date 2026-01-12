# FastAPI Testing - Application-Specific Patterns

FastAPI applications need specialized testing patterns for endpoints, dependencies, middleware, and async handlers. This guide covers patterns specific to FastAPI testing.

**Cross-Skill References**: See **fastapi-builder skill** for endpoint design patterns; see **pytest-testing skill** `fastapi-sqlmodel-testing.md` for testing with database dependencies and SQLModel models.

## FastAPI Testing Setup

### Project Structure for Testing

```
project/
├── src/
│   ├── main.py                  # FastAPI app
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   ├── database.py              # Database setup
│   └── api/
│       ├── endpoints/
│       │   ├── users.py
│       │   ├── products.py
│       │   └── orders.py
│       └── dependencies.py
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── unit/
│   │   ├── test_schemas.py
│   │   └── test_validators.py
│   └── integration/
│       ├── conftest.py
│       └── test_endpoints.py
└── pyproject.toml
```

### FastAPI Test Client Setup

```python
# tests/conftest.py

import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import async_sessionmaker

from src.main import app
from src.database import Base, get_session

# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def test_db():
    """Create in-memory test database"""
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

# ============================================================================
# DEPENDENCY OVERRIDES
# ============================================================================

@pytest.fixture
def override_get_session(test_db):
    """Override FastAPI database dependency"""
    def get_session_override():
        return test_db

    app.dependency_overrides[get_session] = get_session_override
    yield
    del app.dependency_overrides[get_session]

# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def test_client(override_get_session):
    """Sync HTTP client for FastAPI testing"""
    return TestClient(app)

@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client for testing"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

---

## Testing Endpoints

### Testing GET Endpoints

```python
@pytest.mark.asyncio
async def test_get_user_endpoint(async_client, test_user):
    """GET /users/{id} returns user data"""
    response = await async_client.get(f"/api/v1/users/{test_user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
```

### Testing POST Endpoints

```python
@pytest.mark.asyncio
async def test_create_user_endpoint(async_client):
    """POST /users creates new user and returns 201"""
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
    assert "hashed_password" not in data  # Don't expose secrets
```

### Testing PUT/PATCH Endpoints

```python
@pytest.mark.asyncio
async def test_update_user_endpoint(async_client, test_user):
    """PUT /users/{id} updates user"""
    update_data = {
        "email": "updated@example.com",
        "username": "updated_user"
    }

    response = await async_client.put(
        f"/api/v1/users/{test_user.id}",
        json=update_data
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

## Testing Request Validation

### Pydantic Schema Validation

```python
# src/schemas.py

from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

# tests/integration/test_user_endpoints.py

@pytest.mark.asyncio
async def test_create_user_invalid_email(async_client):
    """POST with invalid email returns 422"""
    response = await async_client.post(
        "/api/v1/users",
        json={
            "email": "not-an-email",
            "username": "user",
            "password": "Pass123!"
        }
    )

    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]

@pytest.mark.asyncio
async def test_create_user_missing_field(async_client):
    """POST without required field returns 422"""
    response = await async_client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com"
            # Missing username and password
        }
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("username" in str(e) for e in errors)
```

### Query Parameter Validation

```python
@pytest.mark.asyncio
async def test_list_users_pagination(async_client, multiple_users):
    """GET /users with pagination parameters"""
    response = await async_client.get(
        "/api/v1/users",
        params={"skip": 0, "limit": 10}
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

@pytest.mark.asyncio
async def test_list_users_invalid_limit(async_client):
    """GET with invalid limit returns error"""
    response = await async_client.get(
        "/api/v1/users",
        params={"limit": "invalid"}
    )

    assert response.status_code == 422
```

---

## Testing Authentication & Authorization

### Testing Protected Endpoints

```python
@pytest.fixture
def auth_headers(test_user):
    """Generate JWT headers for test user"""
    from src.core.security import create_access_token

    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_protected_endpoint_without_auth(async_client):
    """Protected endpoint requires authentication"""
    response = await async_client.get("/api/v1/me")

    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

@pytest.mark.asyncio
async def test_protected_endpoint_with_auth(async_client, auth_headers):
    """Protected endpoint returns data with valid token"""
    response = await async_client.get("/api/v1/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

### Testing Login Endpoint

```python
@pytest.mark.asyncio
async def test_login_valid_credentials(async_client, test_user):
    """POST /login with valid credentials returns token"""
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
    """POST /login with wrong password returns 401"""
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

### Testing Permission-Based Authorization

```python
@pytest.fixture
def admin_auth_headers(admin_user):
    """Generate JWT headers for admin user"""
    from src.core.security import create_access_token

    token = create_access_token(str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_admin_only_endpoint_with_user(async_client, auth_headers):
    """Regular user cannot access admin endpoint"""
    response = await async_client.get(
        "/api/v1/admin/users",
        headers=auth_headers
    )

    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_only_endpoint_with_admin(async_client, admin_auth_headers):
    """Admin user can access admin endpoint"""
    response = await async_client.get(
        "/api/v1/admin/users",
        headers=admin_auth_headers
    )

    assert response.status_code == 200
```

---

## Testing Dependencies

### Overriding Dependencies

```python
# src/dependencies.py

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session)
):
    """Get authenticated user"""
    pass

# tests/integration/test_endpoints.py

@pytest.fixture
def override_get_current_user(test_user):
    """Override get_current_user dependency"""
    async def get_current_user_override():
        return test_user

    app.dependency_overrides[get_current_user] = get_current_user_override
    yield
    del app.dependency_overrides[get_current_user]

@pytest.mark.asyncio
async def test_endpoint_with_override(async_client, override_get_current_user):
    """Test endpoint with overridden dependency"""
    response = await async_client.get("/api/v1/me")
    assert response.status_code == 200
```

### Testing with Multiple Dependency Overrides

```python
@pytest.fixture
def override_dependencies(test_user, mock_email_service):
    """Override multiple dependencies"""
    from src.dependencies import get_current_user, get_email_service

    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_email_service] = lambda: mock_email_service

    yield

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_endpoint_uses_dependencies(async_client, override_dependencies):
    """Test endpoint with multiple overridden dependencies"""
    response = await async_client.post(
        "/api/v1/send-welcome-email"
    )

    assert response.status_code == 200
    # Email service was called (if we track it)
```

---

## Testing Error Responses

### Testing Exception Handlers

```python
@pytest.mark.asyncio
async def test_not_found_error(async_client):
    """Non-existent resource returns 404"""
    response = await async_client.get("/api/v1/users/99999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()

@pytest.mark.asyncio
async def test_validation_error(async_client):
    """Invalid input returns 422 with error details"""
    response = await async_client.post(
        "/api/v1/users",
        json={"email": "invalid"}  # Missing fields
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
```

### Testing Custom Exception Handlers

```python
# src/exceptions.py

class BusinessLogicError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code

# src/main.py

@app.exception_handler(BusinessLogicError)
async def business_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# tests/integration/test_error_handling.py

@pytest.mark.asyncio
async def test_business_error_returns_custom_status(async_client):
    """Business logic error returns appropriate status code"""
    # Endpoint raises BusinessLogicError(detail="...", status_code=422)
    response = await async_client.post("/api/v1/process", json={...})

    assert response.status_code == 422
    assert response.json()["detail"] == "Expected error"
```

---

## Testing Middleware

### Testing Custom Middleware

```python
# src/middleware.py

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# tests/integration/test_middleware.py

@pytest.mark.asyncio
async def test_request_id_middleware(async_client):
    """Request ID middleware adds header"""
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 36  # UUID length
```

---

## Testing Background Tasks

### Testing Async Tasks

```python
# src/main.py

@app.post("/api/v1/send-email")
async def send_email(email: EmailSchema, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email_background, email.address)
    return {"message": "Email queued"}

# tests/integration/test_tasks.py

@pytest.mark.asyncio
async def test_email_task_queued(async_client, mocker):
    """Email task is queued on request"""
    mock_send = mocker.patch("src.tasks.send_email_background")

    response = await async_client.post(
        "/api/v1/send-email",
        json={"address": "test@example.com"}
    )

    assert response.status_code == 200
    # Background task was queued (but not executed yet)
```

---

## Testing WebSockets

### WebSocket Connection Testing

```python
from fastapi.testclient import TestClient

@pytest.fixture
def websocket_client():
    """WebSocket test client"""
    return TestClient(app)

def test_websocket_connection(websocket_client):
    """WebSocket can connect and send message"""
    with websocket_client.websocket_connect("/ws") as websocket:
        # Send message
        websocket.send_text("Hello")

        # Receive response
        data = websocket.receive_text()
        assert data == "Hello"

def test_websocket_disconnect(websocket_client):
    """WebSocket handles disconnect gracefully"""
    with websocket_client.websocket_connect("/ws") as websocket:
        websocket.send_text("test")
        # Implicit close on context exit
    # No exception should be raised
```

---

## Testing Streaming Responses

### Testing Streamed Responses

```python
@pytest.mark.asyncio
async def test_streaming_response(async_client):
    """Streaming endpoint returns data chunks"""
    response = await async_client.get("/api/v1/stream")

    assert response.status_code == 200
    # Read streaming content
    chunks = []
    async for chunk in response.aiter_text():
        chunks.append(chunk)

    assert len(chunks) > 0
```

---

## FastAPI Testing Checklist

Before shipping FastAPI tests:

- [ ] All endpoints have GET/POST/PUT/DELETE tests
- [ ] Happy path tested
- [ ] Validation errors tested (422 responses)
- [ ] Authentication tested (with and without token)
- [ ] Authorization tested (permission checks)
- [ ] Error responses tested (404, 500, etc.)
- [ ] Database dependency overridden
- [ ] External service mocks used
- [ ] Response schemas validated
- [ ] Query parameters tested
- [ ] Request body validation tested
- [ ] Async/await properly handled
- [ ] Markers applied (@pytest.mark.integration)
- [ ] Fixtures used for common setup
- [ ] No hardcoded test data

---

## FastAPI Testing Best Practices

### ✅ Do

- **Override dependencies** in tests
- **Test endpoints, not implementation** (test the API contract)
- **Use in-memory database** for fast tests
- **Mock external services** (email, payment, etc.)
- **Test error cases** (validation, auth, not found)
- **Validate response schemas** (check structure)
- **Use proper HTTP methods** (GET vs POST vs PUT)
- **Test status codes** (200, 201, 404, 401, etc.)

### ❌ Don't

- **Test framework internals** (test your endpoints)
- **Use real external APIs** (mock them)
- **Skip validation testing** (edge cases matter)
- **Hardcode user IDs** (use fixtures)
- **Mix sync and async** without handling
- **Expose secrets in responses** (test this)
- **Ignore error paths** (they're important)

---

## Summary

FastAPI Testing Patterns:

- ✅ Override dependencies for controlled testing
- ✅ Use TestClient for sync, AsyncClient for async
- ✅ Test all HTTP methods and status codes
- ✅ Validate request/response schemas
- ✅ Test authentication and authorization
- ✅ Mock external dependencies
- ✅ Test error responses
- ✅ Organize tests by endpoint/feature
