# FastAPI Testing Patterns

## Setup

### Conftest Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app, Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def client(test_db):
    """Override get_db dependency"""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
```

## Route Testing

### Happy Path

```python
import pytest

def test_create_item(client):
    response = client.post(
        "/items/",
        json={"name": "Widget", "price": 9.99}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Widget"
    assert data["price"] == 9.99
    assert "id" in data

def test_list_items(client):
    # Create items
    client.post("/items/", json={"name": "Item1", "price": 10.0})
    client.post("/items/", json={"name": "Item2", "price": 20.0})

    # List items
    response = client.get("/items/?skip=0&limit=10")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2

def test_get_item(client):
    # Create item
    create_response = client.post(
        "/items/",
        json={"name": "Widget", "price": 9.99}
    )
    item_id = create_response.json()["id"]

    # Get item
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["name"] == "Widget"

def test_update_item(client):
    # Create item
    create_response = client.post(
        "/items/",
        json={"name": "Widget", "price": 9.99}
    )
    item_id = create_response.json()["id"]

    # Update item
    response = client.put(
        f"/items/{item_id}",
        json={"name": "Updated Widget", "price": 19.99}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Widget"
    assert data["price"] == 19.99

def test_delete_item(client):
    # Create item
    create_response = client.post(
        "/items/",
        json={"name": "Widget", "price": 9.99}
    )
    item_id = create_response.json()["id"]

    # Delete item
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 200

    # Verify deleted
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 404
```

### Error Cases

```python
def test_create_item_invalid_price(client):
    response = client.post(
        "/items/",
        json={"name": "Widget", "price": -5}  # Negative price
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_get_nonexistent_item(client):
    response = client.get("/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"

def test_update_nonexistent_item(client):
    response = client.put(
        "/items/999",
        json={"name": "Widget", "price": 9.99}
    )
    assert response.status_code == 404

def test_delete_nonexistent_item(client):
    response = client.delete("/items/999")
    assert response.status_code == 404
```

## Authentication Testing

```python
@pytest.fixture
def token(client):
    """Get valid token"""
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    return response.json()["access_token"]

def test_protected_route_with_token(client, token):
    response = client.get(
        "/protected/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_protected_route_without_token(client):
    response = client.get("/protected/")
    assert response.status_code == 403

def test_protected_route_with_invalid_token(client):
    response = client.get(
        "/protected/",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401
```

## Fixtures

```python
@pytest.fixture
def sample_item(client):
    """Create a sample item"""
    response = client.post(
        "/items/",
        json={"name": "Sample", "price": 9.99}
    )
    return response.json()

@pytest.fixture
def sample_user(client):
    """Create a sample user"""
    response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com"}
    )
    return response.json()

@pytest.fixture
def authenticated_client(client, token):
    """Client with authorization header"""
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
```

## Parametrized Tests

```python
@pytest.mark.parametrize("price,valid", [
    (0.01, True),
    (100, True),
    (0, False),
    (-10, False),
])
def test_item_price_validation(client, price, valid):
    response = client.post(
        "/items/",
        json={"name": "Widget", "price": price}
    )
    if valid:
        assert response.status_code == 201
    else:
        assert response.status_code == 422
```

## Best Practices

1. **Test happy path first**: Verify success cases
2. **Test error cases**: Verify validation and error handling
3. **Use fixtures**: Share setup between tests
4. **Mock external services**: Don't call real APIs/databases
5. **Test database transactions**: Verify rollback on error
6. **Test authentication**: Verify token generation and validation
7. **Test pagination**: Verify skip/limit behavior
8. **Use parametrize**: Test multiple inputs efficiently
9. **Keep tests isolated**: Each test should be independent
10. **Mock time**: Use freezegun for time-dependent tests
