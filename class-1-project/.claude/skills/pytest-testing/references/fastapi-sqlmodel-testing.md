# FastAPI SQLModel Testing - Async Database Patterns

Test async database operations with pytest and pytest-asyncio, covering unit tests, integration tests, fixtures, and mocking patterns specific to SQLModel and FastAPI endpoints.

**Cross-Skill References**: See **async-sqlmodel skill** for database layer design, relationship patterns, and performance optimization; see **fastapi-builder skill** for routing and endpoint patterns.

## SQLModel Testing Setup

### Dependencies

```bash
pip install pytest pytest-asyncio httpx sqlalchemy[asyncio] sqlmodel
```

### Test Database Configuration

```python
# tests/conftest.py

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from src.database import get_session
from src.main import app

@pytest_asyncio.fixture
async def test_engine():
    """Create in-memory test database"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    await engine.dispose()

@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test async session"""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

@pytest.fixture
def override_session(test_session):
    """Override FastAPI session dependency"""
    def get_session_override():
        return test_session

    app.dependency_overrides[get_session] = get_session_override
    yield
    del app.dependency_overrides[get_session]
```

---

## Unit Testing SQLModel Services

### Test CRUD Operations

```python
# tests/unit/test_user_service.py

import pytest
from sqlalchemy import select
from sqlmodel import SQLModel
from src.models import User
from src.services.user import UserService

@pytest.mark.asyncio
async def test_create_user(test_session):
    """Test user creation with async session"""
    service = UserService(test_session)
    user = await service.create_user("john", "john@example.com")

    assert user.id is not None
    assert user.username == "john"
    assert user.email == "john@example.com"

@pytest.mark.asyncio
async def test_get_user(test_session):
    """Test retrieving user by ID"""
    # Create user
    user = User(username="jane", email="jane@example.com")
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Retrieve
    service = UserService(test_session)
    retrieved = await service.get_user(user.id)

    assert retrieved is not None
    assert retrieved.username == "jane"

@pytest.mark.asyncio
async def test_update_user(test_session):
    """Test updating user"""
    # Setup
    user = User(username="old", email="old@example.com")
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Update
    service = UserService(test_session)
    updated = await service.update_user(user.id, username="new")

    assert updated.username == "new"

@pytest.mark.asyncio
async def test_delete_user(test_session):
    """Test deleting user"""
    # Setup
    user = User(username="delete_me", email="delete@example.com")
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Delete
    service = UserService(test_session)
    deleted = await service.delete_user(user.id)

    assert deleted is True

    # Verify deleted
    retrieved = await service.get_user(user.id)
    assert retrieved is None
```

---

## Testing Relationships & Eager Loading

### Test Eager Loading

```python
# tests/unit/test_relationships.py

import pytest
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select
from sqlmodel import SQLModel
from src.models import Team, Player

@pytest.mark.asyncio
async def test_eager_load_team_with_players(test_session):
    """Test selectinload for team.players relationship"""
    # Create team with players
    team = Team(name="Dragons")
    test_session.add(team)
    await test_session.flush()

    player1 = Player(name="Alice", team_id=team.id)
    player2 = Player(name="Bob", team_id=team.id)
    test_session.add_all([player1, player2])
    await test_session.commit()

    # Query with eager loading
    statement = select(Team).options(selectinload(Team.players))
    result = await test_session.execute(statement)
    fetched_team = result.unique().scalar_one()

    # Verify relationships loaded
    assert len(fetched_team.players) == 2
    assert {p.name for p in fetched_team.players} == {"Alice", "Bob"}

@pytest.mark.asyncio
async def test_joinedload_player_with_team(test_session):
    """Test joinedload for player.team relationship"""
    # Setup
    team = Team(name="Dragons")
    test_session.add(team)
    await test_session.flush()

    player = Player(name="Alice", team_id=team.id)
    test_session.add(player)
    await test_session.commit()

    # Query with joinedload
    statement = select(Player).options(joinedload(Player.team))
    result = await test_session.execute(statement)
    fetched_player = result.unique().scalar_one()

    # Verify relationship loaded
    assert fetched_player.team.name == "Dragons"

@pytest.mark.asyncio
async def test_lazy_load_fails_without_eager_load(test_session):
    """Test that lazy loading fails in async context"""
    # Setup
    team = Team(name="Dragons")
    test_session.add(team)
    await test_session.flush()

    player = Player(name="Alice", team_id=team.id)
    test_session.add(player)
    await test_session.commit()

    # Query WITHOUT eager loading
    statement = select(Player)
    result = await test_session.execute(statement)
    fetched_player = result.scalar_one()

    # Accessing relationship without eager load raises error
    with pytest.raises(Exception):  # greenlet exception or similar
        _ = fetched_player.team.name
```

---

## Integration Testing FastAPI Endpoints with SQLModel

### Test Endpoints with Async Client

```python
# tests/integration/test_user_endpoints.py

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from src.main import app
from src.models import User
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_user_endpoint(async_client: AsyncClient, override_session):
    """Test POST /users creates user via endpoint"""
    response = await async_client.post(
        "/users/",
        json={"username": "john", "email": "john@example.com", "password": "pass123"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "john"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_get_user_endpoint(async_client: AsyncClient, test_session, override_session):
    """Test GET /users/{id} retrieves user"""
    # Create user in database
    user = User(username="jane", email="jane@example.com")
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Fetch via endpoint
    response = await async_client.get(f"/users/{user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "jane"

@pytest.mark.asyncio
async def test_list_users_pagination(async_client: AsyncClient, test_session, override_session):
    """Test GET /users with pagination"""
    # Create multiple users
    users = [
        User(username=f"user{i}", email=f"user{i}@example.com")
        for i in range(5)
    ]
    test_session.add_all(users)
    await test_session.commit()

    # Fetch with pagination
    response = await async_client.get("/users/?skip=0&limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5

@pytest.mark.asyncio
async def test_update_user_endpoint(async_client: AsyncClient, test_session, override_session):
    """Test PUT /users/{id} updates user"""
    # Create user
    user = User(username="old", email="old@example.com")
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Update via endpoint
    response = await async_client.put(
        f"/users/{user.id}",
        json={"username": "new", "email": "new@example.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "new"

@pytest.mark.asyncio
async def test_delete_user_endpoint(async_client: AsyncClient, test_session, override_session):
    """Test DELETE /users/{id} removes user"""
    # Create user
    user = User(username="delete_me", email="delete@example.com")
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Delete via endpoint
    response = await async_client.delete(f"/users/{user.id}")
    assert response.status_code == 204

    # Verify deleted
    response = await async_client.get(f"/users/{user.id}")
    assert response.status_code == 404
```

---

## Testing Relationships in Endpoints

### Test Endpoint with Eager-Loaded Relationships

```python
# tests/integration/test_relationship_endpoints.py

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from sqlmodel import SQLModel
from src.models import Team, Player

@pytest.mark.asyncio
async def test_get_team_with_players(async_client: AsyncClient, test_session, override_session):
    """Test endpoint returns team with all players"""
    # Create team with players
    team = Team(name="Dragons")
    test_session.add(team)
    await test_session.flush()

    players = [Player(name=f"Player{i}", team_id=team.id) for i in range(3)]
    test_session.add_all(players)
    await test_session.commit()
    await test_session.refresh(team)

    # Fetch via endpoint (endpoint uses eager loading)
    response = await async_client.get(f"/teams/{team.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Dragons"
    assert len(data["players"]) == 3

@pytest.mark.asyncio
async def test_create_player_with_team(async_client: AsyncClient, test_session, override_session):
    """Test creating player assigned to team"""
    # Create team
    team = Team(name="Dragons")
    test_session.add(team)
    await test_session.commit()
    await test_session.refresh(team)

    # Create player via endpoint
    response = await async_client.post(
        "/players/",
        json={"name": "Alice", "team_id": team.id}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["team_id"] == team.id
```

---

## Testing Error Scenarios

### Test SQLModel Constraint Violations

```python
# tests/unit/test_sqlmodel_errors.py

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel
from src.models import User

@pytest.mark.asyncio
async def test_duplicate_username_raises_error(test_session):
    """Test unique constraint on username"""
    # Create first user
    user1 = User(username="john", email="john@example.com")
    test_session.add(user1)
    await test_session.commit()

    # Try to create duplicate
    user2 = User(username="john", email="john2@example.com")
    test_session.add(user2)

    with pytest.raises(IntegrityError):
        await test_session.commit()

@pytest.mark.asyncio
async def test_foreign_key_constraint(test_session):
    """Test foreign key constraint"""
    from src.models import Player

    # Try to create player with non-existent team
    player = Player(name="Alice", team_id=9999)
    test_session.add(player)

    with pytest.raises(IntegrityError):
        await test_session.commit()
```

---

## Testing Async Fixtures

### Create Reusable Fixtures

```python
# tests/conftest.py

import pytest
import pytest_asyncio

@pytest_asyncio.fixture
async def test_user(test_session):
    """Create test user"""
    from src.models import User

    user = User(username="testuser", email="test@example.com")
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_team_with_players(test_session):
    """Create team with players"""
    from src.models import Team, Player

    team = Team(name="TestTeam")
    test_session.add(team)
    await test_session.flush()

    players = [Player(name=f"Player{i}", team_id=team.id) for i in range(3)]
    test_session.add_all(players)
    await test_session.commit()
    await test_session.refresh(team)
    return team

# Use in tests
@pytest.mark.asyncio
async def test_with_fixture(test_user):
    """Test using fixture"""
    assert test_user.username == "testuser"
```

---

## Testing Transactions & Rollback

### Test Transaction Handling

```python
# tests/unit/test_transactions.py

import pytest
from sqlalchemy.exc import IntegrityError
from src.models import User

@pytest.mark.asyncio
async def test_transaction_rollback_on_error(test_session):
    """Test that transaction rolls back on error"""
    # Create valid user
    user1 = User(username="john", email="john@example.com")
    test_session.add(user1)
    await test_session.commit()

    # Try to create duplicate in transaction
    user2 = User(username="john", email="john2@example.com")
    test_session.add(user2)

    with pytest.raises(IntegrityError):
        await test_session.commit()

    await test_session.rollback()

    # Verify only first user exists
    from sqlalchemy import select
    from src.models import User as UserModel

    statement = select(UserModel)
    result = await test_session.execute(statement)
    users = result.scalars().all()

    assert len(users) == 1
    assert users[0].username == "john"
```

---

## Parametrized Tests with SQLModel

### Test Multiple Scenarios

```python
# tests/unit/test_parametrized_sqlmodel.py

import pytest
from src.models import User

@pytest.mark.asyncio
@pytest.mark.parametrize("username,email,expected_valid", [
    ("john", "john@example.com", True),
    ("jane", "jane@example.com", True),
    ("", "invalid@example.com", False),  # Empty username
    ("user", "invalid-email", False),  # Invalid email
])
async def test_user_validation(test_session, username, email, expected_valid):
    """Test user creation with various inputs"""
    user = User(username=username, email=email)
    test_session.add(user)

    if expected_valid:
        await test_session.commit()
        await test_session.refresh(user)
        assert user.id is not None
    else:
        with pytest.raises(Exception):
            await test_session.commit()
```

---

## Mocking External Services with SQLModel

### Mock External API During Database Test

```python
# tests/integration/test_user_with_external_api.py

import pytest
from unittest.mock import AsyncMock, patch
from src.models import User

@pytest.mark.asyncio
async def test_create_user_calls_external_service(test_session, test_client, mocker):
    """Test that creating user calls external service"""
    # Mock external service
    mock_notify = AsyncMock()
    mocker.patch("src.services.send_email", mock_notify)

    # Create user via endpoint
    response = test_client.post(
        "/users/",
        json={"username": "john", "email": "john@example.com", "password": "pass123"}
    )

    assert response.status_code == 201
    mock_notify.assert_called_once()

    # Verify user was created in database
    from sqlalchemy import select
    statement = select(User).where(User.email == "john@example.com")
    result = await test_session.execute(statement)
    user = result.scalar_one_or_none()
    assert user is not None
```

---

## SQLModel Testing Checklist

Before committing tests:
- [ ] All async functions marked with @pytest.mark.asyncio
- [ ] Test database uses in-memory SQLite
- [ ] AsyncSession configured with expire_on_commit=False
- [ ] Relationships tested with eager loading (selectinload/joinedload)
- [ ] No lazy loading in tests
- [ ] Error cases tested (constraints, validation)
- [ ] Fixtures clean up properly
- [ ] Transactions and rollback tested
- [ ] Both unit and integration tests
- [ ] External services mocked
- [ ] Database dependency overridden in endpoint tests
- [ ] Tests are deterministic (same result every run)

---

## Summary

SQLModel testing with pytest requires:
1. **Async fixtures** for test database setup
2. **@pytest.mark.asyncio** marker on all async tests
3. **Eager loading** (selectinload/joinedload) when testing relationships
4. **In-memory database** for fast, isolated tests
5. **Dependency override** for endpoint testing
6. **Error testing** for constraints and validation
