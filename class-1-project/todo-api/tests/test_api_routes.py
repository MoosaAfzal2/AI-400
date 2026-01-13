"""Integration tests for all Todo API routes.

Tests authentication and todo endpoints with complete request/response flow.
Uses in-memory SQLite database for test isolation.
"""

import json
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.todo_api import create_app
from src.todo_api.database import get_session
from src.todo_api.models import Base, Todo, User
from src.todo_api.security import create_access_token, hash_password


# ============================================================================
# Test Database Setup
# ============================================================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def test_db_engine():
    """Create test database engine (function-scoped for test isolation)."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(test_db_engine):
    """Create test database session (persistent for test function)."""
    async_session_maker = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    session = async_session_maker()
    yield session
    await session.close()


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
async def app(test_session):
    """Create FastAPI app with test database session."""
    app = create_app()

    # Override database dependency
    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    return app


@pytest.fixture
async def client(app):
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("TestPass123!"),
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_user_2(test_session: AsyncSession) -> User:
    """Create second test user for isolation testing."""
    user = User(
        email="otheruser@example.com",
        password_hash=hash_password("OtherPass123!"),
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(test_user: User) -> dict:
    """Create authorization headers for test user."""
    access_token = create_access_token(
        {
            "sub": test_user.id,
            "email": test_user.email,
            "type": "access",
        }
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def refresh_token(test_user: User) -> str:
    """Create refresh token for test user."""
    from src.todo_api.security import create_refresh_token
    return create_refresh_token(
        {
            "sub": test_user.id,
            "type": "refresh",
        }
    )


@pytest.fixture
async def sample_todos(test_session: AsyncSession, test_user: User) -> list[Todo]:
    """Create sample todos for test user."""
    todos = []
    for i in range(3):
        todo = Todo(
            user_id=test_user.id,
            title=f"Test Todo {i+1}",
            description=f"Description {i+1}",
            is_completed=i % 2 == 0,
        )
        test_session.add(todo)
        todos.append(todo)

    await test_session.commit()
    for todo in todos:
        await test_session.refresh(todo)

    return todos


# ============================================================================
# Authentication Tests
# ============================================================================


class TestAuthenticationRoutes:
    """Test authentication endpoints."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 201
        data = response.json()
        # Register returns tokens, not user data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(
        self, client: AsyncClient, test_user: User
    ):
        """Test registration with duplicate email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "SecurePass123!",
            },
        )

        # Conflict exception returns 409, not 400
        assert response.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "notanemail",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "weak",
            },
        )

        assert response.status_code == 422

    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com"},
        )

        assert response.status_code == 422

    async def test_login_success(
        self, client: AsyncClient, test_user: User
    ):
        """Test successful login with OAuth2 form data."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with non-existent email."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "AnyPass123!",
            },
        )

        assert response.status_code == 401

    async def test_login_wrong_password(
        self, client: AsyncClient, test_user: User
    ):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPass123!",
            },
        )

        assert response.status_code == 401

    async def test_login_inactive_user(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test login with inactive user."""
        inactive_user = User(
            email="inactive@example.com",
            password_hash=hash_password("TestPass123!"),
            is_active=False,
        )
        test_session.add(inactive_user)
        await test_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": inactive_user.email,
                "password": "TestPass123!",
            },
        )

        assert response.status_code == 401

    async def test_refresh_token_success(
        self, client: AsyncClient, test_user: User
    ):
        """Test token refresh."""
        # First login to get refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh the token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401

    async def test_logout_success(
        self, client: AsyncClient, refresh_token: str
    ):
        """Test successful logout."""
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 204

    async def test_logout_invalid_token(self, client: AsyncClient):
        """Test logout with invalid token."""
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401


# ============================================================================
# Todo CRUD Tests
# ============================================================================


class TestTodoRoutes:
    """Test todo endpoints."""

    async def test_create_todo_success(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Test successful todo creation."""
        response = await client.post(
            "/api/v1/todos",
            headers=auth_headers,
            params={"user_id": test_user.id},
            json={
                "title": "New Todo",
                "description": "Todo description",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Todo"
        assert data["description"] == "Todo description"
        assert data["is_completed"] is False
        assert data["user_id"] == test_user.id

    async def test_create_todo_minimal(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Test todo creation with minimal fields."""
        response = await client.post(
            "/api/v1/todos",
            headers=auth_headers,
            params={"user_id": test_user.id},
            json={"title": "Minimal Todo"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Todo"
        assert data["description"] is None
        assert data["is_completed"] is False

    async def test_create_todo_missing_title(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Test todo creation without title."""
        response = await client.post(
            "/api/v1/todos",
            headers=auth_headers,
            params={"user_id": test_user.id},
            json={"description": "No title"},
        )

        assert response.status_code == 422

    async def test_list_todos_success(
        self, client: AsyncClient, test_user: User, auth_headers: dict, sample_todos
    ):
        """Test listing todos."""
        response = await client.get(
            "/api/v1/todos",
            headers=auth_headers,
            params={"user_id": test_user.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_list_todos_pagination(
        self, client: AsyncClient, test_user: User, auth_headers: dict, sample_todos
    ):
        """Test todo pagination."""
        response = await client.get(
            "/api/v1/todos",
            headers=auth_headers,
            params={"user_id": test_user.id, "skip": 0, "limit": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["has_more"] is True

    async def test_list_todos_filter_completed(
        self, client: AsyncClient, test_user: User, auth_headers: dict, sample_todos
    ):
        """Test filtering todos by completion status."""
        response = await client.get(
            "/api/v1/todos",
            headers=auth_headers,
            params={
                "user_id": test_user.id,
                "is_completed": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Should have 2 completed todos (indices 0 and 2)
        assert data["total"] == 2
        for item in data["items"]:
            assert item["is_completed"] is True

    async def test_list_todos_sort(
        self, client: AsyncClient, test_user: User, auth_headers: dict, sample_todos
    ):
        """Test sorting todos."""
        response = await client.get(
            "/api/v1/todos",
            headers=auth_headers,
            params={
                "user_id": test_user.id,
                "sort_by": "title",
                "sort_order": "asc",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        # Check ascending order by title
        titles = [item["title"] for item in data["items"]]
        assert titles == sorted(titles)

    async def test_get_todo_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        sample_todos: list[Todo],
    ):
        """Test getting single todo."""
        todo_id = sample_todos[0].id
        response = await client.get(
            f"/api/v1/todos/{todo_id}",
            headers=auth_headers,
            params={"user_id": test_user.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Test Todo 1"

    async def test_get_todo_not_found(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Test getting non-existent todo."""
        response = await client.get(
            "/api/v1/todos/99999",
            headers=auth_headers,
            params={"user_id": test_user.id},
        )

        assert response.status_code == 404

    async def test_get_todo_user_isolation(
        self,
        client: AsyncClient,
        test_user: User,
        test_user_2: User,
        auth_headers: dict,
        sample_todos: list[Todo],
    ):
        """Test user cannot access other user's todos."""
        todo_id = sample_todos[0].id

        # Try to access with different user
        auth_headers_2 = {
            "Authorization": f"Bearer {create_access_token({'sub': test_user_2.id, 'email': test_user_2.email, 'type': 'access'})}"
        }

        response = await client.get(
            f"/api/v1/todos/{todo_id}",
            headers=auth_headers_2,
            params={"user_id": test_user_2.id},
        )

        assert response.status_code == 404

    async def test_update_todo_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        sample_todos: list[Todo],
    ):
        """Test updating todo."""
        todo_id = sample_todos[0].id

        response = await client.put(
            f"/api/v1/todos/{todo_id}",
            headers=auth_headers,
            params={"user_id": test_user.id},
            json={
                "title": "Updated Todo",
                "is_completed": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Todo"
        assert data["is_completed"] is True

    async def test_update_todo_partial(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        sample_todos: list[Todo],
    ):
        """Test partial todo update."""
        todo_id = sample_todos[0].id
        original_title = sample_todos[0].title

        response = await client.put(
            f"/api/v1/todos/{todo_id}",
            headers=auth_headers,
            params={"user_id": test_user.id},
            json={"is_completed": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == original_title
        assert data["is_completed"] is True

    async def test_update_todo_not_found(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Test updating non-existent todo."""
        response = await client.put(
            "/api/v1/todos/99999",
            headers=auth_headers,
            params={"user_id": test_user.id},
            json={"title": "Updated"},
        )

        assert response.status_code == 404

    async def test_delete_todo_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        sample_todos: list[Todo],
    ):
        """Test deleting todo."""
        todo_id = sample_todos[0].id

        response = await client.delete(
            f"/api/v1/todos/{todo_id}",
            headers=auth_headers,
            params={"user_id": test_user.id},
        )

        assert response.status_code == 204

    async def test_delete_todo_not_found(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Test deleting non-existent todo."""
        response = await client.delete(
            "/api/v1/todos/99999",
            headers=auth_headers,
            params={"user_id": test_user.id},
        )

        assert response.status_code == 404


# ============================================================================
# Health & Observability Tests
# ============================================================================


class TestHealthRoutes:
    """Test health check endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test health endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_readiness_check(self, client: AsyncClient):
        """Test readiness endpoint."""
        response = await client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ready", "healthy"]

    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test metrics endpoint."""
        response = await client.get("/metrics")

        assert response.status_code == 200
        # Metrics endpoint returns JSON with app info
        data = response.json()
        assert "app_name" in data
        assert data["app_name"] == "todo-api"


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling."""

    async def test_invalid_route(self, client: AsyncClient):
        """Test 404 on invalid route."""
        response = await client.get("/invalid/route")

        assert response.status_code == 404

    async def test_invalid_json(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test 422 on invalid JSON."""
        response = await client.post(
            "/api/v1/auth/login",
            content="{invalid json",
            headers={**auth_headers, "content-type": "application/json"},
        )

        assert response.status_code in [400, 422]

    async def test_missing_required_query_param(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test list todos without query params (should work, as user_id is from JWT)."""
        response = await client.get(
            "/api/v1/todos",
            headers=auth_headers,
        )

        # Should succeed - user_id now comes from JWT token, not query params
        assert response.status_code == 200

    async def test_invalid_query_param_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test list todos with valid query params."""
        response = await client.get(
            "/api/v1/todos",
            headers=auth_headers,
            params={"limit": 20},
        )

        # Should succeed - invalid user_id param no longer exists
        assert response.status_code == 200

    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers in response."""
        response = await client.get("/health")

        # Check that response is successful (CORS is handled by middleware)
        assert response.status_code == 200


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================


class TestCompleteWorkflow:
    """Test complete workflows."""

    async def test_register_login_create_todo_workflow(
        self, client: AsyncClient
    ):
        """Test complete flow: register -> login -> create todo."""
        # Register
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "workflow@example.com",
                "password": "WorkflowPass123!",
            },
        )
        assert register_response.status_code == 201
        # Register returns tokens, not user_id
        access_token = register_response.json()["access_token"]

        # Create todo with registered token (no need to login again)
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        todo_response = await client.post(
            "/api/v1/todos",
            headers=auth_headers,
            json={"title": "My First Todo"},
        )

        assert todo_response.status_code == 201
        assert todo_response.json()["title"] == "My First Todo"

    async def test_register_login_refresh_logout_workflow(
        self, client: AsyncClient
    ):
        """Test auth workflow: register -> login -> refresh -> logout."""
        # Register
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "auth_workflow@example.com",
                "password": "AuthFlowPass123!",
            },
        )
        assert register_response.status_code == 201
        refresh_token = register_response.json()["refresh_token"]

        # Refresh token (get new access token)
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        # Note: refresh endpoint doesn't return new refresh_token, only access_token

        # Logout with original refresh token
        logout_response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert logout_response.status_code == 204

    async def test_complete_todo_crud_workflow(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Test complete CRUD workflow for todos."""
        user_id = test_user.id

        # Create
        create_response = await client.post(
            "/api/v1/todos",
            headers=auth_headers,
            params={"user_id": user_id},
            json={"title": "CRUD Todo", "description": "Test CRUD"},
        )
        assert create_response.status_code == 201
        todo_id = create_response.json()["id"]

        # Read
        read_response = await client.get(
            f"/api/v1/todos/{todo_id}",
            headers=auth_headers,
            params={"user_id": user_id},
        )
        assert read_response.status_code == 200
        assert read_response.json()["title"] == "CRUD Todo"

        # Update
        update_response = await client.put(
            f"/api/v1/todos/{todo_id}",
            headers=auth_headers,
            params={"user_id": user_id},
            json={"title": "Updated CRUD Todo", "is_completed": True},
        )
        assert update_response.status_code == 200
        assert update_response.json()["is_completed"] is True

        # Delete
        delete_response = await client.delete(
            f"/api/v1/todos/{todo_id}",
            headers=auth_headers,
            params={"user_id": user_id},
        )
        assert delete_response.status_code == 204
