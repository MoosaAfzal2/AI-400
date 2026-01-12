# Mocking and Patching - Testing Patterns

Mocking isolates code under test by replacing external dependencies with controlled test doubles. This prevents flaky tests and enables testing error scenarios.

## Mocking Overview

### Why Mock?

```
Without Mocking:
┌─────────────┐     ┌──────────┐     ┌─────────────┐
│  Your Code  │────▶│ Database │────▶│  External   │
│   (Tests)   │     │          │     │    API      │
└─────────────┘     └──────────┘     └─────────────┘
                         ↓
                    - Slow
                    - Flaky
                    - Hard to control

With Mocking:
┌─────────────┐     ┌──────────┐     ┌─────────────┐
│  Your Code  │────▶│   Mock   │────▶│   Mock      │
│   (Tests)   │     │ Database │     │   API       │
└─────────────┘     └──────────┘     └─────────────┘
                         ↓
                    - Fast
                    - Deterministic
                    - Full control
```

### Mock vs Stub vs Spy

| Type | Purpose | Returns | Can Assert |
|------|---------|---------|------------|
| **Mock** | Replace dependency | Configured value | Yes (calls, args) |
| **Stub** | Provide test data | Fixed return value | No |
| **Spy** | Wrap real object | Real + track calls | Yes (calls only) |

---

## unittest.mock Basics

### Simple Mock

```python
from unittest.mock import Mock

def test_simple_mock():
    """Create and use a simple mock"""
    mock_db = Mock()
    mock_db.get_user.return_value = {"id": 1, "name": "John"}

    result = mock_db.get_user(1)

    assert result == {"id": 1, "name": "John"}
    mock_db.get_user.assert_called_once_with(1)
```

### Mock Return Values

```python
from unittest.mock import Mock

def test_mock_return_values():
    """Configure different return values"""
    mock_api = Mock()

    # Single return value
    mock_api.fetch.return_value = {"status": "ok"}

    # Multiple calls return different values
    mock_api.process.side_effect = [
        {"result": 1},
        {"result": 2},
        Exception("Failed")
    ]

    assert mock_api.fetch() == {"status": "ok"}
    assert mock_api.process() == {"result": 1}
    assert mock_api.process() == {"result": 2}

    try:
        mock_api.process()
    except Exception as e:
        assert str(e) == "Failed"
```

### Asserting Mock Calls

```python
from unittest.mock import Mock

def test_mock_call_assertions():
    """Verify mock was called correctly"""
    mock_service = Mock()

    # Call the mock
    mock_service.save_user({"name": "John"})

    # Assertions
    mock_service.save_user.assert_called()
    mock_service.save_user.assert_called_once()
    mock_service.save_user.assert_called_with({"name": "John"})

    # Check call count
    assert mock_service.save_user.call_count == 1

    # Get call arguments
    call_args = mock_service.save_user.call_args
    assert call_args[0][0]["name"] == "John"
```

---

## Patching (unittest.mock.patch)

### Basic Patching

```python
from unittest.mock import patch

def test_patch_function():
    """Patch a function during test"""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"user": "test"}

        from src.services import fetch_user_from_api
        result = fetch_user_from_api(1)

        assert result["user"] == "test"
        mock_get.assert_called_once()
```

### Patch Decorator

```python
from unittest.mock import patch

@patch("src.services.EmailService.send")
def test_email_sent(mock_send):
    """Patch function using decorator"""
    mock_send.return_value = True

    from src.services import notify_user
    result = notify_user("user@example.com")

    assert result is True
    mock_send.assert_called_once_with("user@example.com")
```

### Patch Multiple Targets

```python
from unittest.mock import patch

@patch("src.services.PaymentAPI.charge")
@patch("src.services.EmailService.send")
def test_payment_flow(mock_email, mock_charge):
    """Patch multiple functions"""
    mock_charge.return_value = {"transaction_id": "123"}
    mock_email.return_value = True

    from src.services import process_payment
    result = process_payment(user_id=1, amount=99.99)

    assert result["status"] == "success"
    mock_charge.assert_called_once()
    mock_email.assert_called_once()
```

### Patch with Context Manager

```python
from unittest.mock import patch

def test_patch_context_manager():
    """Use patch as context manager"""
    with patch("src.config.get_settings") as mock_settings:
        mock_settings.return_value.debug = True

        from src.main import app
        assert app.debug is True

    # Patch only applies within context
```

---

## pytest-mock Fixture

### Using pytest-mock

```python
def test_with_pytest_mock(mocker):
    """Use pytest-mock fixture"""
    mock_db = mocker.Mock()
    mock_db.get_user.return_value = {"id": 1}

    # Use mock_db
    result = mock_db.get_user(1)

    assert result["id"] == 1
    mock_db.get_user.assert_called_once_with(1)
```

### Patching with pytest-mock

```python
def test_patch_with_mocker(mocker):
    """Patch using pytest-mock"""
    mocker.patch("requests.get", return_value={"status": "ok"})

    from src.services import call_external_api
    result = call_external_api()

    assert result["status"] == "ok"
```

### Spy with pytest-mock

```python
def test_spy_with_mocker(mocker):
    """Spy on real function to track calls"""
    spy = mocker.spy(some_module, "real_function")

    from src.services import process
    process()

    spy.assert_called()
```

---

## Mocking Async Functions

### Mock AsyncMock

```python
from unittest.mock import AsyncMock

async def test_async_mock():
    """Mock async function"""
    mock_db = AsyncMock()
    mock_db.get_user.return_value = {"id": 1, "email": "test@example.com"}

    result = await mock_db.get_user(1)

    assert result["email"] == "test@example.com"
    mock_db.get_user.assert_called_once_with(1)
```

### Patching Async Functions

```python
from unittest.mock import patch, AsyncMock

@patch("src.database.Database.fetch_user", new_callable=AsyncMock)
async def test_patch_async(mock_fetch):
    """Patch async function"""
    mock_fetch.return_value = {"id": 1, "name": "John"}

    from src.services import UserService
    service = UserService()
    user = await service.get_user(1)

    assert user["name"] == "John"
    mock_fetch.assert_called_once_with(1)
```

### pytest-mock with Async

```python
@pytest.mark.asyncio
async def test_async_with_mocker(mocker):
    """Use pytest-mock with async"""
    mock_api = mocker.AsyncMock()
    mock_api.fetch.return_value = {"data": "test"}

    result = await mock_api.fetch()

    assert result["data"] == "test"
```

---

## Monkeypatch

### Monkeypatch Fixture

```python
def test_monkeypatch_environment(monkeypatch):
    """Monkeypatch to modify environment"""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")

    from src.config import get_database_url
    url = get_database_url()

    assert url == "sqlite:///test.db"
```

### Monkeypatch Object Attributes

```python
def test_monkeypatch_attribute(monkeypatch):
    """Monkeypatch object attributes"""
    class Config:
        debug = False

    monkeypatch.setattr(Config, "debug", True)

    assert Config.debug is True
```

### Monkeypatch Functions

```python
def test_monkeypatch_function(monkeypatch):
    """Monkeypatch function implementation"""
    def mock_validate(email):
        return True

    monkeypatch.setattr(
        "src.validators.validate_email",
        mock_validate
    )

    from src.validators import validate_email
    assert validate_email("anything") is True
```

---

## Mocking Classes

### Mock Class Instance

```python
from unittest.mock import Mock

def test_mock_class_instance():
    """Mock a class and its instance"""
    MockUser = Mock()
    mock_instance = MockUser.return_value

    mock_instance.email = "test@example.com"
    mock_instance.save.return_value = True

    user = MockUser()
    assert user.email == "test@example.com"
    assert user.save() is True

    MockUser.assert_called_once()
```

### Mock Class with MagicMock

```python
from unittest.mock import MagicMock, patch

@patch("src.models.User")
def test_mock_class(MockUser):
    """Mock entire class"""
    MockUser.return_value.id = 1
    MockUser.return_value.email = "test@example.com"

    from src.models import User
    user = User()

    assert user.id == 1
    assert user.email == "test@example.com"
```

---

## Freezegun (Time Mocking)

### Mock Datetime

```python
from freezegun import freeze_time
from datetime import datetime

@freeze_time("2024-01-15 10:00:00")
def test_with_frozen_time():
    """Freeze time for deterministic testing"""
    now = datetime.now()

    assert now.year == 2024
    assert now.month == 1
    assert now.day == 15
```

### Testing Time-Based Logic

```python
from freezegun import freeze_time
from datetime import datetime, timedelta

@freeze_time("2024-01-01")
def test_token_expiration():
    """Test token expiration with frozen time"""
    from src.core.security import create_access_token

    token = create_access_token(user_id=1)
    created = datetime.now()

    # Move time forward
    with freeze_time("2024-01-02"):
        from src.core.security import verify_token
        # Token should be expired
        with pytest.raises(TokenExpiredError):
            verify_token(token)
```

### Testing Retry Logic with Time

```python
from freezegun import freeze_time

@freeze_time("2024-01-01 10:00:00")
def test_retry_with_backoff():
    """Test retry logic with time progression"""
    from src.services import retry_with_backoff

    call_count = 0

    def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary failure")
        return "success"

    # Simulate retries with time progression
    from freezegun import freeze_time
    with freeze_time("2024-01-01 10:00:00"):
        result = retry_with_backoff(failing_function, max_retries=3)
        assert result == "success"
        assert call_count == 3
```

---

## Common Mocking Patterns

### Mocking Database Session

```python
from unittest.mock import Mock

def test_service_with_mock_database():
    """Mock database for service testing"""
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = \
        {"id": 1, "email": "test@example.com"}

    from src.services import UserService
    service = UserService(db=mock_db)
    user = service.get_user(1)

    assert user["email"] == "test@example.com"
```

### Mocking External API

```python
from unittest.mock import patch

@patch("requests.get")
def test_external_api_call(mock_get):
    """Mock external HTTP API"""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "id": 1,
        "name": "Product"
    }

    from src.services import get_product
    product = get_product(1)

    assert product["name"] == "Product"
    mock_get.assert_called_once()
```

### Mocking File Operations

```python
from unittest.mock import mock_open, patch

@patch("builtins.open", new_callable=mock_open, read_data="file content")
def test_file_reading(mock_file):
    """Mock file operations"""
    from src.utils import read_file

    content = read_file("test.txt")

    assert content == "file content"
    mock_file.assert_called_once_with("test.txt", "r")
```

### Mocking Logger

```python
from unittest.mock import patch

@patch("src.logger.logger")
def test_logging(mock_logger):
    """Mock logger to verify logging"""
    from src.services import process_user

    process_user({"id": 1, "email": "test@example.com"})

    mock_logger.info.assert_called()
    call_args = mock_logger.info.call_args
    assert "test@example.com" in str(call_args)
```

---

## Side Effects & Exceptions

### Raising Exceptions

```python
from unittest.mock import Mock

def test_mock_raises_exception():
    """Mock that raises exception"""
    mock_service = Mock()
    mock_service.fetch.side_effect = ConnectionError("Network timeout")

    with pytest.raises(ConnectionError):
        mock_service.fetch()
```

### Different Return Values Per Call

```python
from unittest.mock import Mock

def test_side_effect_sequence():
    """Mock returns different values on each call"""
    mock_api = Mock()
    mock_api.call.side_effect = [
        {"status": "processing"},
        {"status": "processing"},
        {"status": "complete"}
    ]

    assert mock_api.call()["status"] == "processing"
    assert mock_api.call()["status"] == "processing"
    assert mock_api.call()["status"] == "complete"
```

### Side Effect Function

```python
from unittest.mock import Mock

def test_side_effect_function():
    """Mock with custom function"""
    def custom_side_effect(x):
        return x * 2

    mock_func = Mock(side_effect=custom_side_effect)

    assert mock_func(5) == 10
    assert mock_func(3) == 6
```

---

## Advanced Mocking

### Partial Mocking (Wraps)

```python
from unittest.mock import Mock

def test_partial_mock_with_wraps():
    """Mock that wraps and tracks real implementation"""
    real_function = lambda x: x + 1

    mock = Mock(wraps=real_function)
    result = mock(5)

    assert result == 6  # Real behavior
    mock.assert_called_once_with(5)  # Tracking
```

### Mock Spec

```python
from unittest.mock import Mock

class RealService:
    def get_data(self): pass
    def save_data(self, data): pass

def test_mock_with_spec():
    """Mock enforces spec of real class"""
    mock = Mock(spec=RealService)

    mock.get_data()
    mock.save_data({"key": "value"})

    # This would fail:
    # mock.nonexistent_method()  # AttributeError
```

### Reset Mock

```python
from unittest.mock import Mock

def test_reset_mock():
    """Reset mock between operations"""
    mock = Mock()

    mock.method1()
    assert mock.method1.call_count == 1

    mock.reset_mock()
    assert mock.method1.call_count == 0
```

---

## Mocking Best Practices

### ✅ Do

- **Mock external dependencies** (APIs, databases, file system)
- **Use appropriate mock type** (Mock, AsyncMock, MagicMock)
- **Verify meaningful behavior** (not implementation details)
- **Use fixtures for common mocks** (reuse patterns)
- **Clear naming** (mock_*, test_*)
- **Patch at import point** (where used, not where defined)
- **Reset mocks** between tests (isolate state)

### ❌ Don't

- **Mock everything** (only external dependencies)
- **Mock code under test** (test the real thing)
- **Over-assert** (too many call verifications)
- **Hardcode mock returns** (use fixtures or factories)
- **Leave mocks global** (scope properly)
- **Mock standard library** (unless truly isolated)
- **Forget to assert** (mock assertions verify mock was used)

---

## Mocking Checklist

Before committing mocked tests:

- [ ] Only external dependencies are mocked
- [ ] Mocks have clear, descriptive names
- [ ] Mock return values are realistic
- [ ] Test asserts mock was called appropriately
- [ ] Error scenarios tested with side_effect
- [ ] Async functions use AsyncMock
- [ ] Time-dependent code uses freezegun
- [ ] Fixtures used for common mock patterns
- [ ] Mocks are reset between tests
- [ ] Tests are deterministic (no flakiness)
