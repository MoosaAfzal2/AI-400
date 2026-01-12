# Testing Architecture - Production-Grade Test Suite

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_security.py     # Password hashing, JWT
│   ├── test_schemas.py      # Pydantic validation
│   └── __init__.py
├── integration/
│   ├── test_auth_endpoints.py
│   ├── test_user_endpoints.py
│   ├── test_admin_endpoints.py
│   └── __init__.py
└── __init__.py
```

## Pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["src"]           # Add src to Python path
testpaths = ["tests"]          # Test discovery directory
asyncio_mode = "auto"          # Auto-detect async fixtures
addopts = "-v --cov=src --cov-report=html"  # Coverage reporting
```

## Fixtures (conftest.py)

### Database Fixture

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="function")
async def test_db():
    """In-memory SQLite database for tests"""
    # Use in-memory SQLite for speed and isolation
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Provide session
    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
def override_get_db(test_db):
    """Override FastAPI dependency"""
    def get_db_override():
        return test_db

    app.dependency_overrides[get_db] = get_db_override
    yield
    del app.dependency_overrides[get_db]
```

### Client Fixture

```python
@pytest.fixture
def client(override_get_db):
    """FastAPI test client with overridden dependencies"""
    from fastapi.testclient import TestClient
    return TestClient(app)
```

### Authentication Fixture

```python
@pytest.fixture
async def test_user(test_db):
    """Create test user in database"""
    from src.auth_service.core.security import hash_password

    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("TestPassword123!"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Generate JWT token for test user"""
    from src.auth_service.core.security import create_access_token

    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}
```

---

## Unit Tests

### Security Tests (test_security.py)

```python
import pytest
from src.auth_service.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)

class TestPasswordHashing:
    """Test password hashing with bcrypt"""

    def test_hash_password_creates_hash(self):
        """Verify bcrypt creates a hash different from input"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) == 60  # Bcrypt hash length

    def test_verify_password_correct(self):
        """Verify correct password matches"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Verify incorrect password doesn't match"""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_same_password(self):
        """Verify different salt creates different hash"""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different due to salt
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

class TestJWTTokens:
    """Test JWT token generation and verification"""

    def test_create_access_token(self):
        """Verify access token creation"""
        user_id = uuid4()
        token = create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 100

    def test_verify_access_token_valid(self):
        """Verify valid access token decodes"""
        user_id = uuid4()
        token = create_access_token(user_id)

        payload = verify_token(token, token_type="access")

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_verify_token_wrong_type(self):
        """Verify wrong token type raises error"""
        user_id = uuid4()
        access_token = create_access_token(user_id)

        with pytest.raises(HTTPException):
            verify_token(access_token, token_type="refresh")

    def test_verify_expired_token(self):
        """Verify expired token raises error"""
        user_id = uuid4()
        # Create token with past expiration (not realistic but for testing)
        token = create_access_token(user_id)

        # Manually modify exp claim to past time
        from jose import jwt
        private_key, _ = get_rsa_keys()
        past_payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
        }
        expired_token = jwt.encode(past_payload, private_key, algorithm="RS256")

        with pytest.raises(HTTPException) as exc:
            verify_token(expired_token, token_type="access")
        assert exc.value.status_code == 401

class TestRefreshTokenGeneration:
    """Test refresh token lifecycle"""

    def test_create_refresh_token(self):
        """Verify refresh token creation"""
        user_id = uuid4()
        token = create_refresh_token(user_id)

        assert isinstance(token, str)
        payload = verify_token(token, token_type="refresh")
        assert payload["sub"] == str(user_id)
```

### Schema Validation Tests (test_schemas.py)

```python
import pytest
from pydantic import ValidationError
from src.auth_service.schemas import UserCreate, ResetPasswordRequest

class TestUserCreateSchema:
    """Test user registration schema validation"""

    def test_valid_user_create(self):
        """Verify valid user data passes"""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="SecurePassword123!",
        )
        assert user.email == "test@example.com"

    def test_invalid_email(self):
        """Verify invalid email rejected"""
        with pytest.raises(ValidationError) as exc:
            UserCreate(
                email="not-an-email",
                username="testuser",
                password="SecurePassword123!",
            )
        assert "email" in str(exc.value)

    def test_username_too_short(self):
        """Verify username minimum length"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="ab",  # Too short
                password="SecurePassword123!",
            )

    def test_password_too_weak(self):
        """Verify password strength requirements"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="weak",  # Too short and weak
            )
```

---

## Integration Tests

### Authentication Endpoint Tests (test_auth_endpoints.py)

```python
import pytest
from fastapi.testclient import TestClient

class TestSignUp:
    """Test user registration endpoint"""

    def test_sign_up_success(self, client):
        """Verify successful user registration"""
        response = client.post(
            "/api/v1/sign-up",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePassword123!",
                "first_name": "New",
                "last_name": "User",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"

    def test_sign_up_duplicate_email(self, client, test_user):
        """Verify duplicate email rejected"""
        response = client.post(
            "/api/v1/sign-up",
            json={
                "email": test_user.email,  # Same as existing
                "username": "different",
                "password": "SecurePassword123!",
            }
        )

        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]

    def test_sign_up_invalid_email(self, client):
        """Verify invalid email rejected"""
        response = client.post(
            "/api/v1/sign-up",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "SecurePassword123!",
            }
        )

        assert response.status_code == 422

class TestLogin:
    """Test login endpoint"""

    def test_login_success(self, client, test_user):
        """Verify successful login"""
        response = client.post(
            "/api/v1/login",
            data={
                "username": test_user.email,
                "password": "TestPassword123!",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_password(self, client, test_user):
        """Verify invalid password rejected"""
        response = client.post(
            "/api/v1/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!",
            }
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Verify nonexistent user rejected"""
        response = client.post(
            "/api/v1/login",
            data={
                "username": "nonexistent@example.com",
                "password": "Password123!",
            }
        )

        assert response.status_code == 401

class TestLogout:
    """Test logout endpoint"""

    def test_logout_success(self, client, auth_headers):
        """Verify successful logout"""
        response = client.post(
            "/api/v1/logout",
            headers=auth_headers,
        )

        assert response.status_code == 204  # No content

    def test_logout_invalid_token(self, client):
        """Verify logout without token"""
        response = client.post(
            "/api/v1/logout",
            headers={"Authorization": "Bearer invalid"},
        )

        assert response.status_code == 401

class TestRefresh:
    """Test refresh token endpoint"""

    @pytest.mark.asyncio
    async def test_refresh_success(self, client, test_db, test_user, auth_headers):
        """Verify token refresh"""
        # Create and store refresh token
        from src.auth_service.core.security import create_refresh_token
        refresh_token = create_refresh_token(test_user.id)

        token_obj = RefreshToken(
            token=refresh_token,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        test_db.add(token_obj)
        await test_db.commit()

        # Refresh
        response = client.post(
            "/api/v1/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] != auth_headers["Authorization"].split()[1]

    def test_refresh_invalid_token(self, client):
        """Verify refresh with invalid token fails"""
        response = client.post(
            "/api/v1/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_security.py

# Run specific test class
pytest tests/unit/test_security.py::TestPasswordHashing

# Run specific test
pytest tests/unit/test_security.py::TestPasswordHashing::test_hash_password_creates_hash

# Run with output
pytest -v

# Run and stop on first failure
pytest -x

# Run integration tests only
pytest tests/integration/

# Run with markers
pytest -m "not slow"
```

---

## Markers for Organization

```python
import pytest

# Mark slow tests
@pytest.mark.slow
def test_expensive_operation():
    pass

# Mark integration tests
@pytest.mark.integration
def test_endpoint():
    pass

# Run without slow tests
# pytest -m "not slow"
```

---

## Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html

# Show coverage in terminal
pytest --cov=src --cov-report=term-missing
```

---

## Test Best Practices

- ✅ Each test tests one thing
- ✅ Use descriptive test names
- ✅ Arrange-Act-Assert pattern
- ✅ Fixtures for setup/teardown
- ✅ Mock external services
- ✅ Test error cases
- ✅ Use in-memory database for speed
- ✅ Isolate tests (no interdependencies)
- ✅ Aim for 80%+ coverage on critical paths
- ✅ Test integration points (API endpoints)
