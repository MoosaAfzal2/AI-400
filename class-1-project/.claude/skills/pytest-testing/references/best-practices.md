# Test Organization & Best Practices

Professional test suites follow patterns that make them maintainable, readable, and reliable. This guide covers test organization, naming conventions, common pitfalls, and production-grade practices.

## Test Organization

### Directory Structure

```
tests/
├── __init__.py                      # Mark as package
├── conftest.py                      # Root fixtures (shared across all tests)
├── unit/                            # Unit tests (isolated, fast)
│   ├── __init__.py
│   ├── conftest.py                  # Unit-specific fixtures
│   ├── test_models.py               # Test data models
│   ├── test_validators.py           # Test validation logic
│   ├── test_utils.py                # Test utility functions
│   └── test_auth.py                 # Test auth functions
├── integration/                     # Integration tests (with services)
│   ├── __init__.py
│   ├── conftest.py                  # Integration-specific fixtures
│   ├── test_user_endpoints.py       # Test user API endpoints
│   ├── test_product_endpoints.py    # Test product API endpoints
│   └── test_workflows.py            # Test multi-step workflows
├── e2e/                             # End-to-end tests (full flows)
│   ├── __init__.py
│   └── test_user_journey.py         # Test complete user journey
└── fixtures/                        # Shared test data (optional)
    ├── users.py                     # User test fixtures
    └── products.py                  # Product test fixtures
```

### Test File Organization

```python
# tests/unit/test_validators.py

"""Unit tests for validation functions.

This module tests validation logic for:
- Email addresses
- Passwords
- User input
"""

import pytest
from src.validators import (
    validate_email,
    validate_password,
    validate_username,
)

# ============================================================================
# Email Validation Tests
# ============================================================================

def test_valid_email_accepted():
    """Valid email passes validation"""
    assert validate_email("user@example.com") is True

def test_invalid_email_rejected():
    """Invalid email fails validation"""
    assert validate_email("invalid.email") is False

# ============================================================================
# Password Validation Tests
# ============================================================================

def test_password_minimum_length():
    """Password must meet minimum length"""
    assert validate_password("short1!") is False
    assert validate_password("validpass123!") is True

# ============================================================================
# Username Validation Tests
# ============================================================================

class TestUsernameValidation:
    """Test username validation rules"""

    def test_valid_username(self):
        assert validate_username("john_doe") is True

    def test_username_too_short(self):
        assert validate_username("ab") is False
```

---

## Naming Conventions

### Test Function Naming

```python
# ✅ Good - Clear, descriptive, testable behavior
def test_valid_email_passes_validation():
    pass

def test_invalid_email_fails_validation():
    pass

def test_short_password_rejected():
    pass

# ❌ Bad - Vague, doesn't describe what's tested
def test_email():
    pass

def test_validation():
    pass

def test_function():
    pass
```

### Test Class Naming

```python
# ✅ Good - Groups related tests, clear purpose
class TestEmailValidation:
    def test_valid_email(self):
        pass

class TestPasswordValidation:
    def test_minimum_length(self):
        pass

# ❌ Bad - Generic, doesn't organize clearly
class TestValidators:
    def test_1(self):
        pass

    def test_2(self):
        pass
```

### Fixture Naming

```python
# ✅ Good - Descriptive, clear what it provides
@pytest.fixture
def valid_user_data():
    return {...}

@pytest.fixture
def authenticated_client():
    return client

@pytest.fixture
def test_database():
    return db

# ❌ Bad - Generic or cryptic
@pytest.fixture
def data():
    return {...}

@pytest.fixture
def x():
    return client
```

---

## Test Structure (AAA Pattern)

Every test should follow Arrange-Act-Assert:

### Arrange-Act-Assert Pattern

```python
def test_user_creation_success():
    """User can be created with valid data"""
    # ARRANGE - Set up test data and conditions
    user_data = {
        "email": "new@example.com",
        "username": "newuser",
        "password": "Password123!"
    }

    # ACT - Execute the code being tested
    user = User.create(**user_data)

    # ASSERT - Verify the result
    assert user.email == "new@example.com"
    assert user.id is not None
```

### Single Assertion Focus

```python
# ✅ Good - One behavior per test
def test_user_email_stored_correctly():
    user = User(email="test@example.com")
    assert user.email == "test@example.com"

def test_user_id_generated():
    user = User(email="test@example.com")
    assert user.id is not None

# ❌ Bad - Multiple unrelated assertions
def test_user():
    user = User(email="test@example.com")
    assert user.email == "test@example.com"
    assert user.id is not None
    assert user.is_active is True
    assert user.created_at is not None  # Too many things!
```

---

## Parameterization for Coverage

### Avoid Test Duplication with Parametrization

```python
# ❌ Bad - Repeated test code
def test_email_validation_1():
    assert validate_email("valid@example.com") is True

def test_email_validation_2():
    assert validate_email("another@test.com") is True

def test_email_validation_3():
    assert validate_email("invalid.email") is False

# ✅ Good - Parameterized
@pytest.mark.parametrize("email,expected", [
    ("valid@example.com", True),
    ("another@test.com", True),
    ("invalid.email", False),
])
def test_email_validation(email, expected):
    assert validate_email(email) == expected
```

### Parametrization with IDs for Clarity

```python
@pytest.mark.parametrize("password,is_strong", [
    ("WeakPass1", False),
    ("Strong@Pass123", True),
    ("AnotherWeak", False),
], ids=["weak_short", "strong_complete", "weak_no_special"])
def test_password_strength(password, is_strong):
    assert is_strong_password(password) == is_strong
```

---

## Fixtures Best Practices

### Organize Fixtures by Scope

```python
# tests/conftest.py - Root fixtures (shared by all tests)

@pytest.fixture(scope="session")
def event_loop():
    """Event loop for entire test session"""
    pass

@pytest.fixture(scope="function")
def test_database():
    """Fresh database for each test"""
    pass

# tests/unit/conftest.py - Unit test fixtures

@pytest.fixture
def mock_db():
    """Mock database for unit tests"""
    return Mock()

# tests/integration/conftest.py - Integration fixtures

@pytest.fixture(scope="function")
async def async_client():
    """AsyncClient for integration tests"""
    pass
```

### Clear Fixture Dependencies

```python
# ✅ Good - Clear dependency chain
@pytest.fixture
def test_database():
    """Create test database"""
    return setup_database()

@pytest.fixture
def test_user(test_database):
    """Create test user in database"""
    user = User(email="test@example.com")
    test_database.add(user)
    test_database.commit()
    return user

@pytest.fixture
def auth_headers(test_user):
    """Generate auth headers for test user"""
    token = create_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}

# ❌ Bad - Unclear dependencies
@pytest.fixture
def setup():
    # Does everything
    pass
```

### Fixture Naming Matches Purpose

```python
# ✅ Good - Name clearly indicates what fixture provides
@pytest.fixture
def admin_user_with_permissions():
    return create_user(is_admin=True)

@pytest.fixture
def postgres_database():
    return connect_to_postgres()

# ❌ Bad - Generic names
@pytest.fixture
def user1():
    pass

@pytest.fixture
def db():
    pass
```

---

## Markers & Test Categorization

### Using Markers Effectively

```python
# pytest.ini
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (with services)",
    "e2e: End-to-end tests (full flow)",
    "slow: Slow running tests",
    "db: Tests requiring database",
    "auth: Authentication tests",
]
```

### Applying Markers

```python
@pytest.mark.unit
def test_validate_email():
    """Fast unit test"""
    pass

@pytest.mark.integration
@pytest.mark.db
def test_create_user_in_database():
    """Integration test needing database"""
    pass

@pytest.mark.e2e
@pytest.mark.slow
def test_complete_user_journey():
    """Slow end-to-end test"""
    pass
```

### Running by Marker

```bash
# Run only unit tests
pytest -m unit

# Run integration tests but not slow ones
pytest -m "integration and not slow"

# Run tests requiring database
pytest -m db
```

---

## Error Handling & Assertions

### Testing Errors Effectively

```python
# ✅ Good - Specific exception and message
def test_invalid_email_raises_validation_error():
    """Invalid email raises specific error"""
    with pytest.raises(ValidationError, match="Invalid email format"):
        validate_email("invalid")

# ❌ Bad - Too generic
def test_invalid_email_raises_error():
    with pytest.raises(Exception):  # Too broad
        validate_email("invalid")
```

### Clear Assertion Messages

```python
# ✅ Good - Assertion messages clarify intent
def test_user_list_not_empty(users):
    assert len(users) > 0, "User list should contain at least one user"

# ❌ Bad - No message or unclear
def test_user_list(users):
    assert len(users) > 0
```

---

## Avoiding Common Pitfalls

### Avoiding Order Dependencies

```python
# ❌ Bad - Tests depend on execution order
@pytest.mark.order(1)
def test_create_user():
    global_user_id = create_user("test")

@pytest.mark.order(2)
def test_update_user():
    update_user(global_user_id)  # Depends on test_create_user

# ✅ Good - Each test is independent
def test_create_user(test_database):
    user = create_user("test", db=test_database)
    assert user.id is not None

def test_update_user(test_database, test_user):
    update_user(test_user.id, db=test_database)
    # Uses fixture, not global state
```

### Avoiding Flaky Tests

```python
# ❌ Bad - Uses real time, flaky
def test_timeout():
    import time
    start = time.time()
    operation()
    elapsed = time.time() - start
    assert elapsed < 0.1  # Timing is unreliable

# ✅ Good - Mock time
@freeze_time("2024-01-01")
def test_timeout():
    with freeze_time("2024-01-01 00:00:01"):
        result = operation()
        assert result is not None
```

### Avoiding Hardcoded Test Data

```python
# ❌ Bad - Hardcoded data
def test_user_creation():
    user = User(email="hardcoded@example.com")
    assert user.email == "hardcoded@example.com"

# ✅ Good - Parameterized or fixture-based
@pytest.mark.parametrize("email", [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com",
])
def test_user_creation(email):
    user = User(email=email)
    assert user.email == email
```

### Avoiding Silent Failures

```python
# ❌ Bad - Silently catches exception
def test_with_exception_handling():
    try:
        operation()
    except:
        pass  # Silent failure!
    assert True

# ✅ Good - Explicit exception testing
def test_with_explicit_exception():
    with pytest.raises(ExpectedException):
        operation()
```

---

## Documentation & Comments

### Clear Test Docstrings

```python
def test_email_validation_accepts_valid_format():
    """Valid email addresses pass validation.

    Email validation should accept:
    - Standard format: user@domain.com
    - Subdomains: user@subdomain.domain.com
    - Plus addressing: user+tag@domain.com

    This test verifies standard format acceptance.
    """
    assert validate_email("user@example.com") is True
```

### When to Add Comments

```python
# ✅ Good - Comments explain why, not what
def test_database_constraint():
    user1 = User(email="test@example.com")
    db.add(user1)
    db.commit()

    # Email is unique, so second user with same email fails
    user2 = User(email="test@example.com")
    db.add(user2)

    with pytest.raises(IntegrityError):
        db.commit()

# ❌ Bad - Comments state the obvious
def test_database_constraint():
    # Create first user
    user1 = User(email="test@example.com")
    # Add to database
    db.add(user1)
    # Commit
    db.commit()
```

---

## Test Maintenance

### Keeping Tests DRY (Don't Repeat Yourself)

```python
# ❌ Bad - Repeated assertions in multiple tests
def test_user_1():
    user = User(email="test1@example.com")
    assert user.email is not None
    assert len(user.email) > 0
    assert "@" in user.email

def test_user_2():
    user = User(email="test2@example.com")
    assert user.email is not None
    assert len(user.email) > 0
    assert "@" in user.email

# ✅ Good - Extract to helper or fixture
@pytest.fixture
def user(email):
    user = User(email=email)
    assert_valid_email(user.email)
    return user

def assert_valid_email(email):
    assert email is not None
    assert len(email) > 0
    assert "@" in email
```

### Updating Tests with Code Changes

```python
# When you change implementation, update tests too
# ✅ Good - Test updated with implementation
def format_user_name(user):
    """Returns 'LastName, FirstName'"""
    return f"{user.last_name}, {user.first_name}"

def test_format_user_name():
    user = User(first_name="John", last_name="Doe")
    # Updated to match new format
    assert format_user_name(user) == "Doe, John"
```

---

## Test Quality Checklist

Before committing tests:

### Naming & Organization
- [ ] Test file is in correct directory (unit/integration/e2e)
- [ ] Test file is named `test_*.py` or `*_test.py`
- [ ] Test functions are named `test_*`
- [ ] Function names describe what's being tested
- [ ] Test classes are named `Test*` and group related tests

### Structure & Clarity
- [ ] Each test follows Arrange-Act-Assert pattern
- [ ] Test has clear docstring explaining purpose
- [ ] Test focuses on one behavior
- [ ] Assertions are meaningful and have context
- [ ] No hardcoded magic numbers or strings

### Coverage & Edge Cases
- [ ] Happy path test exists
- [ ] Edge cases are tested (empty, null, boundary)
- [ ] Error cases are tested
- [ ] Parametrization used for multiple inputs
- [ ] Coverage meets target (80%+)

### Fixtures & Dependencies
- [ ] Fixtures are used for common setup
- [ ] Fixtures have clear, descriptive names
- [ ] No test interdependencies
- [ ] External dependencies are mocked
- [ ] Fixtures are properly scoped

### Markers & Organization
- [ ] Tests are marked appropriately (@pytest.mark.unit, etc.)
- [ ] Slow tests are marked (@pytest.mark.slow)
- [ ] Database tests are marked (@pytest.mark.db)
- [ ] Tests can be run by category

### Quality & Maintainability
- [ ] No test duplication (use parametrization)
- [ ] No sleep() or time.sleep()
- [ ] No global state or shared variables
- [ ] Tests are deterministic
- [ ] Tests run consistently (not flaky)

---

## Production Test Practices

### Continuous Integration

```bash
# Run on every commit
pytest --cov=src --cov-fail-under=80 -m "not slow"

# Run full suite on PR
pytest --cov=src --cov-report=html

# Run slow tests separately (e.g., nightly)
pytest -m slow
```

### Monitoring Test Health

```python
# Track test flakiness
# Re-run failed tests once automatically
pytest --lf  # Run last failed
pytest --ff  # Failed first

# Run with timeout to catch hangs
pytest --timeout=5
```

### Documentation

```python
# Maintain a README for test structure
# tests/README.md documents:
# - How to run tests
# - How tests are organized
# - How to add new tests
# - Common patterns used
```

---

## Summary

Professional test suites:

- ✅ Are organized by type (unit/integration/e2e)
- ✅ Use clear, descriptive naming
- ✅ Follow AAA pattern (Arrange-Act-Assert)
- ✅ Focus on one behavior per test
- ✅ Use fixtures for common setup
- ✅ Mock external dependencies
- ✅ Test both happy and error paths
- ✅ Are deterministic and fast
- ✅ Are maintainable and DRY
- ✅ Measure and maintain coverage
