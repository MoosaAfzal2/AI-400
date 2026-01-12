# Pytest Configuration - Setup & Best Practices

## pytest.ini vs pyproject.toml vs tox.ini

### Modern Approach: pyproject.toml (Recommended)

```toml
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["src"]                    # Add src to Python path
testpaths = ["tests"]                   # Where to discover tests
python_files = ["test_*.py", "*_test.py"]  # Test file patterns
python_classes = ["Test*"]              # Test class patterns
python_functions = ["test_*"]           # Test function patterns

# Asyncio configuration
asyncio_mode = "auto"                   # Auto-detect async fixtures

# Output options
addopts = "-v --strict-markers --tb=short"
markers = [
    "unit: unit tests",
    "integration: integration tests",
    "e2e: end-to-end tests",
    "slow: slow running tests",
]

# Coverage options
[tool.coverage.run]
source = ["src"]
omit = ["*/migrations/*", "*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

### Legacy: pytest.ini

```ini
[pytest]
pythonpath = src
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

asyncio_mode = auto

addopts = -v --strict-markers --tb=short

markers =
    unit: unit tests
    integration: integration tests
    e2e: end-to-end tests
    slow: slow running tests
```

---

## conftest.py Structure

### Root conftest.py (tests/conftest.py)

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
import httpx
from fastapi.testclient import TestClient

# Project imports
from src.database import Base, get_session
from src.main import app

# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Called before test collection begins"""
    print("\n" + "="*70)
    print("Starting Test Suite")
    print("="*70)

def pytest_collection_modifyitems(config, items):
    """Add markers to test items"""
    for item in items:
        # Auto-mark slow tests
        if "slow" in item.nodeid:
            item.add_marker(pytest.mark.slow)

# ============================================================================
# ASYNC FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_db():
    """In-memory SQLite database for tests"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

# ============================================================================
# DEPENDENCY OVERRIDES
# ============================================================================

@pytest.fixture(def override_get_session(test_db):
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
    """FastAPI TestClient with dependencies overridden"""
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Async HTTP client for testing"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

# ============================================================================
# AUTH FIXTURES
# ============================================================================

@pytest.fixture
async def test_user(test_db):
    """Create test user in database"""
    from src.models import User
    from src.core.security import hash_password
    from uuid import uuid4

    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Generate JWT token headers for test user"""
    from src.core.security import create_access_token

    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}

```

### Unit Test conftest.py (tests/unit/conftest.py)

```python
import pytest
from unittest.mock import Mock, MagicMock

@pytest.fixture
def mock_db():
    """Mock database session"""
    return MagicMock()

@pytest.fixture
def mock_email_service():
    """Mock email service"""
    return MagicMock()
```

### Integration Test conftest.py (tests/integration/conftest.py)

```python
import pytest

# Integration-specific fixtures here
# Usually inherits session fixtures from root conftest.py
```

---

## Pytest Plugins Setup

### Installation

```bash
# Core testing
pip install pytest                    # Test framework
pip install pytest-asyncio            # Async support
pip install pytest-cov                # Coverage

# Useful additions
pip install pytest-mock               # Mock fixture
pip install pytest-timeout            # Timeout tests
pip install pytest-xdist              # Parallel execution
pip install freezegun                 # Mock datetime
pip install faker                     # Generate test data
```

### pyproject.toml with Plugins

```toml
[project]
dependencies = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "pytest-mock>=3.10",
    "pytest-timeout>=2.1",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
timeout = 5                    # Global timeout
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

---

## Test Discovery

### File/Function Naming Convention

```
tests/
├── unit/
│   ├── test_auth.py           # test_*.py pattern
│   └── test_models.py
├── integration/
│   ├── test_endpoints.py
│   └── test_workflows.py
└── conftest.py

# Inside files:
def test_happy_path():        # test_* pattern
    ...

class TestUserModel:          # Test* pattern
    def test_create_user(self):
        ...
```

### Custom Discovery

```ini
# pytest.ini - only discover specific patterns
python_files = test_*.py custom_*_tests.py
python_classes = Test* Custom*
python_functions = test_* custom_test_*
```

---

## Running Pytest

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/unit/test_auth.py

# Run specific test
pytest tests/unit/test_auth.py::test_login_success

# Run specific test class
pytest tests/unit/test_auth.py::TestUserAuth

# Run matching pattern
pytest -k "login"             # Tests with "login" in name

# Run with markers
pytest -m unit                # Only unit tests
pytest -m "not slow"          # Skip slow tests
```

### Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# Show coverage in terminal
pytest --cov=src --cov-report=term-missing

# Set minimum coverage threshold
pytest --cov=src --cov-fail-under=80
```

### Parallel Execution

```bash
# Run tests in parallel (install pytest-xdist)
pytest -n auto                # Use all CPU cores
pytest -n 4                   # Use 4 processes
```

### Debug Mode

```bash
# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Drop into debugger on errors
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb

# Show local variables on failure
pytest -l
```

---

## Pytest Markers

### Built-in Markers

```python
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+")
def test_new_syntax():
    pass

@pytest.mark.xfail(reason="Known bug in library")
def test_known_issue():
    pass
```

### Custom Markers (in pytest.ini)

```ini
markers =
    unit: unit tests (fast, isolated)
    integration: integration tests (use DB/services)
    e2e: end-to-end tests (full flow)
    slow: slow running tests
    network: tests requiring network
    db: tests requiring database
```

### Usage

```python
@pytest.mark.unit
def test_password_hash():
    pass

@pytest.mark.integration
@pytest.mark.db
def test_create_user():
    pass

@pytest.mark.slow
def test_expensive_operation():
    pass
```

---

## Pytest Hooks (Advanced)

```python
# conftest.py

def pytest_runtest_setup(item):
    """Run before each test"""
    print(f"\nSetting up: {item.name}")

def pytest_runtest_teardown(item, nextitem):
    """Run after each test"""
    print(f"\nTearing down: {item.name}")

def pytest_exception_interact(node, call, report):
    """Called when test raises exception"""
    if report.failed:
        print(f"Test failed: {call.excinfo}")

def pytest_assertrepr_compare(config, op, left, right):
    """Custom assertion message"""
    if isinstance(left, dict) and isinstance(right, dict):
        return [f"Dict comparison: {left} {op} {right}"]
```

---

## Best Practices

✅ **Do:**
- Keep conftest.py focused and organized
- Use function scope by default (fastest)
- Use markers for test categorization
- Group related fixtures in conftest.py
- Parametrize for multiple test variations
- Use pytest plugins for common tasks

❌ **Don't:**
- Hardcode paths (use pytest paths config)
- Skip tests without reason
- Create global state in fixtures
- Mix sync and async tests without handling
- Ignore flaky tests (fix root cause)
