# Unit Testing - Pytest Patterns

Unit tests isolate and verify individual functions, methods, and classes. They are fast, deterministic, and form the foundation of a test suite.

## Unit Test Basics

### Anatomy of a Unit Test

```python
# tests/unit/test_auth.py

def test_password_validation_success():
    """Test happy path: valid password"""
    from src.core.security import validate_password

    # Arrange - Setup
    password = "SecurePassword123!"

    # Act - Execute
    is_valid = validate_password(password)

    # Assert - Verify
    assert is_valid is True
```

### Test Organization

```
tests/
├── unit/                          # Unit tests only
│   ├── test_auth.py              # Test auth module
│   ├── test_models.py            # Test data models
│   ├── test_validators.py        # Test validation functions
│   └── conftest.py               # Fixtures for unit tests
├── integration/                   # Integration tests
└── conftest.py                   # Root fixtures
```

---

## Happy Path Tests

Test the expected, successful behavior:

### Simple Function Test

```python
def test_hash_password_creates_hash():
    """Hash function returns non-empty string"""
    from src.core.security import hash_password

    password = "MyPassword123!"
    hashed = hash_password(password)

    assert hashed is not None
    assert len(hashed) > 0
    assert hashed != password  # Not plaintext
```

### Class Method Test

```python
class TestUserModel:
    """Test User model"""

    def test_user_creation(self):
        """User can be created with email and username"""
        from src.models import User

        user = User(
            email="test@example.com",
            username="testuser"
        )

        assert user.email == "test@example.com"
        assert user.username == "testuser"

    def test_user_full_name_property(self):
        """Full name combines first and last name"""
        from src.models import User

        user = User(
            first_name="John",
            last_name="Doe"
        )

        assert user.full_name == "John Doe"
```

---

## Edge Cases & Boundary Tests

Test limits, boundary conditions, and unusual valid inputs:

### Boundary Values

```python
def test_password_length_validation():
    """Test password minimum/maximum length"""
    from src.core.security import validate_password

    # Too short (boundary)
    assert validate_password("Short1!") is False

    # Minimum valid (boundary)
    assert validate_password("MinValid1!") is True

    # Very long (boundary)
    assert validate_password("A" * 256 + "123!") is True

    # Exactly at limit (boundary)
    assert validate_password("Valid12345678901!") is True
```

### Empty/None Inputs

```python
def test_email_validation_edge_cases():
    """Test email validation with edge cases"""
    from src.validators import validate_email

    # Empty string
    assert validate_email("") is False

    # None (if function handles)
    try:
        validate_email(None)
    except TypeError:
        pass  # Expected

    # Whitespace
    assert validate_email("   ") is False

    # Only special characters
    assert validate_email("@@@") is False
```

### Collections (Empty, Single, Multiple)

```python
def test_list_processing():
    """Test function with different list sizes"""
    from src.utils import sum_positive_numbers

    # Empty list
    assert sum_positive_numbers([]) == 0

    # Single element
    assert sum_positive_numbers([5]) == 5

    # Multiple elements
    assert sum_positive_numbers([1, 2, 3]) == 6

    # Mixed positive/negative
    assert sum_positive_numbers([1, -2, 3]) == 4
```

---

## Error & Exception Tests

Verify that functions fail correctly with invalid inputs:

### Basic Exception Testing

```python
import pytest

def test_division_by_zero_raises_error():
    """Division by zero raises ValueError"""
    from src.math_utils import safe_divide

    with pytest.raises(ValueError, match="Cannot divide by zero"):
        safe_divide(10, 0)
```

### Testing Error Messages

```python
def test_invalid_email_error_message():
    """Invalid email raises exception with helpful message"""
    from src.validators import validate_email_strict

    with pytest.raises(ValueError) as exc_info:
        validate_email_strict("not-an-email")

    assert "Invalid email format" in str(exc_info.value)
    assert "must contain @" in str(exc_info.value)
```

### Multiple Exception Types

```python
def test_file_operations_errors():
    """File operations raise appropriate errors"""
    from src.file_utils import read_file

    # File not found
    with pytest.raises(FileNotFoundError):
        read_file("/nonexistent/file.txt")

    # Permission denied
    with pytest.raises(PermissionError):
        read_file("/root/protected.txt")

    # Invalid input type
    with pytest.raises(TypeError):
        read_file(123)  # Not a string
```

---

## Parametrized Tests

Test multiple inputs with one test function:

### Simple Parametrization

```python
import pytest

@pytest.mark.parametrize("input_email,expected", [
    ("valid@example.com", True),
    ("another.email@domain.co.uk", True),
    ("invalid.email", False),
    ("@example.com", False),
    ("user@", False),
])
def test_email_validation_parametrized(input_email, expected):
    """Email validation for multiple inputs"""
    from src.validators import is_valid_email

    assert is_valid_email(input_email) == expected
```

### Parametrization with IDs

```python
@pytest.mark.parametrize("password,is_strong", [
    ("WeakPass1", False),
    ("Strong@Pass123", True),
    ("AnotherWeak", False),
    ("VeryStr0ng!Password", True),
], ids=["weak_short", "strong_complete", "weak_no_special", "strong_long"])
def test_password_strength_parametrized(password, is_strong):
    """Password strength checker for different patterns"""
    from src.validators import is_strong_password

    assert is_strong_password(password) == is_strong
```

### Parametrization with Tuples (Multiple Parameters)

```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_addition_parametrized(a, b, expected):
    """Addition for multiple number pairs"""
    from src.math_utils import add

    assert add(a, b) == expected
```

### Parametrization with Complex Objects

```python
from dataclasses import dataclass

@dataclass
class UserInput:
    email: str
    username: str
    password: str

@pytest.mark.parametrize("user_data", [
    UserInput("test@example.com", "testuser", "Pass123!"),
    UserInput("admin@example.com", "admin", "AdminPass123!"),
    UserInput("user@example.com", "user", "UserPass123!"),
])
def test_user_creation_parametrized(user_data):
    """User creation for different user types"""
    from src.models import User

    user = User(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password
    )

    assert user.email == user_data.email
```

---

## Fixtures for Unit Tests

Reusable setup for unit tests:

### Simple Data Fixtures

```python
# tests/unit/conftest.py

import pytest

@pytest.fixture
def valid_user_data():
    """Valid user data for tests"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePassword123!",
    }

@pytest.fixture
def valid_email():
    """Valid email address"""
    return "test@example.com"

# Usage in test
def test_email_validation(valid_email):
    """Test with fixture data"""
    from src.validators import is_valid_email

    assert is_valid_email(valid_email) is True
```

### Object Fixtures

```python
@pytest.fixture
def user_model(valid_user_data):
    """Create User model instance"""
    from src.models import User

    return User(**valid_user_data)

def test_user_has_email(user_model):
    """Test user object has email"""
    assert user_model.email == "test@example.com"
```

### Mock Data Fixtures

```python
@pytest.fixture
def mock_users():
    """Multiple test users"""
    from src.models import User

    return [
        User(email=f"user{i}@example.com", username=f"user{i}")
        for i in range(5)
    ]

def test_user_list_processing(mock_users):
    """Test processing list of users"""
    assert len(mock_users) == 5
    assert all(isinstance(u, User) for u in mock_users)
```

---

## Mocking in Unit Tests

Isolate code under test by mocking dependencies:

### Mock Simple Dependencies

```python
from unittest.mock import Mock

def test_user_service_with_mock_database():
    """Test user service with mocked database"""
    from src.services import UserService

    # Create mock
    mock_db = Mock()
    mock_db.get_user.return_value = {
        "id": 1,
        "email": "test@example.com"
    }

    # Use with service
    service = UserService(db=mock_db)
    user = service.get_user(1)

    # Verify
    assert user["email"] == "test@example.com"
    mock_db.get_user.assert_called_once_with(1)
```

### Mock Function Calls

```python
from unittest.mock import patch

def test_email_sending():
    """Test email sending calls external service"""
    from src.services import EmailService

    with patch("src.services.send_email_via_smtp") as mock_send:
        mock_send.return_value = True

        service = EmailService()
        result = service.send("test@example.com", "Hello")

        assert result is True
        mock_send.assert_called_once()
```

### Mock with Side Effects

```python
from unittest.mock import Mock

def test_retry_logic():
    """Test retry logic with failing then succeeding mock"""
    from src.services import RetryService

    mock_api = Mock()
    # Fail first call, succeed second
    mock_api.fetch.side_effect = [
        Exception("Timeout"),
        {"data": "success"}
    ]

    service = RetryService(api=mock_api)
    result = service.fetch_with_retry()

    assert result["data"] == "success"
    assert mock_api.fetch.call_count == 2
```

---

## Assertions & Introspection

### Basic Assertions

```python
def test_basic_assertions():
    """Common assertion patterns"""
    result = [1, 2, 3]

    # Equality
    assert result == [1, 2, 3]
    assert result != []

    # Truthiness
    assert result  # Non-empty list is truthy
    assert not []  # Empty list is falsy

    # Type
    assert isinstance(result, list)
    assert isinstance(result[0], int)

    # Membership
    assert 1 in result
    assert 4 not in result

    # Comparison
    assert len(result) > 0
    assert len(result) <= 3
```

### String Assertions

```python
def test_string_assertions():
    """String-specific assertions"""
    message = "Hello World"

    # Substring
    assert "World" in message
    assert "Hello" in message

    # Case
    assert message.startswith("Hello")
    assert message.endswith("World")

    # Length
    assert len(message) == 11

    # Match (requires pytest regex)
    import re
    assert re.search(r"World", message)
```

### Dictionary Assertions

```python
def test_dict_assertions():
    """Dictionary-specific assertions"""
    user = {"name": "John", "age": 30, "email": "john@example.com"}

    # Keys and values
    assert "name" in user
    assert user["name"] == "John"

    # Structure
    assert user.get("email") == "john@example.com"
    assert user.get("missing") is None

    # Subset
    assert {"name": "John"}.items() <= user.items()
```

### Approximate Comparisons

```python
def test_approximate_assertions():
    """Test floating point numbers approximately"""
    pi = 3.14159

    # Absolute tolerance
    assert pi == pytest.approx(3.14, abs=0.01)

    # Relative tolerance
    assert pi == pytest.approx(3.1, rel=0.01)

    # Lists of floats
    assert [1.1, 2.2, 3.3] == pytest.approx([1.1, 2.2, 3.3], abs=0.01)
```

---

## Test Isolation & Independence

### Avoiding Test Interdependencies

```python
# ❌ Bad - Tests depend on execution order
class TestBadOrder:
    def test_01_create_user(self):
        # Creates state
        global_user_id = create_user("test")

    def test_02_get_user(self):
        # Depends on test_01
        user = get_user(global_user_id)

# ✅ Good - Each test is independent
class TestGoodIsolation:
    def test_create_user(self, db_session):
        """Create user with fresh database"""
        user = create_user("test")
        assert user.id is not None

    def test_get_user(self, db_session, test_user):
        """Get user with fixture setup"""
        user = get_user(test_user.id)
        assert user.email == test_user.email
```

### Using Fixtures for Isolation

```python
@pytest.fixture(autouse=True)
def cleanup():
    """Automatically cleanup after each test"""
    yield
    # Cleanup code runs after test
    clear_temp_files()
    reset_mock_calls()
```

---

## Best Practices for Unit Tests

### ✅ Do

- **One assertion focus**: Test one behavior per test
- **Clear names**: Describe what's being tested
- **DRY with fixtures**: Reuse common setup
- **Test behavior, not implementation**: What it does, not how
- **Use parametrization**: Multiple inputs with one test
- **Mock external dependencies**: Keep tests fast and isolated
- **Test error cases**: Invalid inputs, exceptions
- **Keep tests small**: Easy to understand and fix

### ❌ Don't

- **Multiple assertions on unrelated things**: Keep focus
- **Shared state between tests**: Use fixtures instead
- **Sleep/time waits**: Makes tests slow and flaky
- **Test implementation details**: Test public interface
- **Hardcode test data**: Use factories or fixtures
- **Skip without reason**: Fix flaky tests
- **Ignore edge cases**: Boundary values matter
- **Test framework itself**: Test your code

---

## Unit Test Checklist

Before committing unit tests:

- [ ] Each test has clear, descriptive name
- [ ] Test focuses on one behavior
- [ ] Happy path test exists
- [ ] Edge cases tested
- [ ] Error cases tested
- [ ] Fixtures used for common setup
- [ ] No test interdependencies
- [ ] All assertions are meaningful
- [ ] Mocks isolate external dependencies
- [ ] Tests are deterministic (same result every run)
- [ ] Run `pytest --cov` and check coverage
