# FastAPI Integration - Using Async SQLModel in Endpoints

Integrate async SQLModel database layer with FastAPI endpoints using dependency injection, proper session management, and error handling.

**Cross-Skill References**: See **fastapi-builder skill** for routing patterns and API design; see **pytest-testing skill** `fastapi-sqlmodel-testing.md` for testing endpoints with database dependencies.

## Session Dependency

### Basic Session Dependency

```python
# src/database.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import async_session_maker

async def get_session() -> AsyncSession:
    """Provide AsyncSession for endpoints"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Using in Endpoints

```python
# src/api/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.models import User
from src.services import user_service

router = APIRouter()

@router.post("/users/", response_model=dict)
async def create_user(
    username: str,
    email: str,
    session: AsyncSession = Depends(get_session),
):
    """Create new user"""
    user = await user_service.create_user(
        session=session,
        username=username,
        email=email,
    )
    return {"id": user.id, "username": user.username}

@router.get("/users/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get user by ID"""
    user = await user_service.get_user(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username}
```

---

## CRUD Endpoints

### Create Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

router = APIRouter()

@router.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create new user"""
    user = User(username=user_in.username, email=user_in.email)
    session.add(user)

    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )
```

### Read Endpoint (Single)

```python
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get user by ID"""
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
```

### Read Endpoint (List with Pagination)

```python
from typing import List

class PaginatedResponse(BaseModel):
    items: List[UserResponse]
    total: int
    skip: int
    limit: int

@router.get("/users/", response_model=PaginatedResponse)
async def list_users(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
):
    """List users with pagination"""
    # Get total count
    count_statement = select(func.count(User.id))
    count_result = await session.execute(count_statement)
    total = count_result.scalar()

    # Get paginated results
    statement = select(User).offset(skip).limit(limit)
    result = await session.execute(statement)
    users = result.scalars().all()

    return PaginatedResponse(
        items=users,
        total=total,
        skip=skip,
        limit=limit,
    )
```

### Update Endpoint

```python
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update user"""
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update only provided fields
    if user_in.username is not None:
        user.username = user_in.username
    if user_in.email is not None:
        user.email = user_in.email

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

### Delete Endpoint

```python
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete user"""
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await session.delete(user)
    await session.commit()
```

---

## Handling Relationships in Endpoints

### Get with Related Data

```python
from sqlalchemy.orm import selectinload

@router.get("/teams/{team_id}", response_model=TeamWithPlayers)
async def get_team_with_players(
    team_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get team with all players (eager loaded)"""
    statement = (
        select(Team)
        .where(Team.id == team_id)
        .options(selectinload(Team.players))
    )
    result = await session.execute(statement)
    team = result.unique().scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    return team
```

### Create with Relationship

```python
class PlayerCreate(BaseModel):
    name: str
    team_id: int

@router.post("/players/", response_model=PlayerResponse)
async def create_player(
    player_in: PlayerCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create player and assign to team"""
    # Verify team exists
    team = await session.get(Team, player_in.team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team not found",
        )

    player = Player(name=player_in.name, team_id=player_in.team_id)
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player
```

---

## Error Handling

### Catch Database Errors

```python
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

@router.post("/users/", response_model=UserResponse)
async def create_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create user with comprehensive error handling"""
    try:
        user = User(username=user_in.username, email=user_in.email)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    except IntegrityError as e:
        await session.rollback()
        if "username" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
        elif "email" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate entry",
            )

    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error",
        )
```

---

## Filtering & Search

### Query Parameters Filtering

```python
from typing import Optional

@router.get("/users/")
async def list_users(
    skip: int = 0,
    limit: int = 10,
    username: Optional[str] = None,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    session: AsyncSession = Depends(get_session),
):
    """List users with filtering"""
    statement = select(User)

    # Build filters
    filters = []
    if username:
        filters.append(User.username.ilike(f"%{username}%"))
    if email:
        filters.append(User.email == email)
    if is_active is not None:
        filters.append(User.is_active == is_active)

    if filters:
        from sqlalchemy import and_
        statement = statement.where(and_(*filters))

    # Add pagination
    statement = statement.offset(skip).limit(limit)

    # Execute
    result = await session.execute(statement)
    users = result.scalars().all()

    return users
```

---

## Lifespan Events

### Setup & Teardown

```python
# src/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Setup and teardown events"""
    # Startup
    print("🚀 Starting up...")
    await init_db()

    # Serve requests
    yield

    # Shutdown
    print("🛑 Shutting down...")
    await close_db()

app = FastAPI(lifespan=lifespan)

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
```

---

## Dependency Overrides for Testing

### Override Session in Tests

```python
# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_session

@pytest.fixture
def test_client(test_session):
    """Override session dependency"""
    def override_get_session():
        return test_session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    del app.dependency_overrides[get_session]

# Use in tests
def test_create_user(test_client):
    response = test_client.post(
        "/users/",
        json={"username": "john", "email": "john@example.com"}
    )
    assert response.status_code == 201
```

---

## Batch Operations

### Bulk Create

```python
from typing import List

class BulkUserCreate(BaseModel):
    users: List[UserCreate]

@router.post("/users/bulk/", response_model=List[UserResponse])
async def bulk_create_users(
    bulk_in: BulkUserCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create multiple users"""
    users = [
        User(username=u.username, email=u.email)
        for u in bulk_in.users
    ]

    session.add_all(users)
    await session.commit()

    # Refresh all to get IDs
    for user in users:
        await session.refresh(user)

    return users
```

---

## Streaming Responses

### Stream Large Results

```python
from fastapi.responses import StreamingResponse
import json

@router.get("/users/stream/")
async def stream_users(
    session: AsyncSession = Depends(get_session),
):
    """Stream all users (memory efficient)"""
    async def generate():
        statement = select(User)
        result = await session.stream(statement)

        yield "[\n"
        first = True

        async for user in result.scalars():
            if not first:
                yield ",\n"
            yield json.dumps({
                "id": user.id,
                "username": user.username,
                "email": user.email,
            })
            first = False

        yield "\n]"
        await session.close()

    return StreamingResponse(generate(), media_type="application/json")
```

---

## FastAPI Integration Checklist

Before deploying endpoints:

- [ ] Session dependency created and used in all endpoints
- [ ] Error handling for IntegrityError and SQLAlchemyError
- [ ] Proper HTTP status codes (201 for create, 404 for not found, etc.)
- [ ] Relationships eagerly loaded with selectinload/joinedload
- [ ] Circular relationship dependencies handled in response models
- [ ] Pagination implemented for list endpoints
- [ ] Filtering available for search endpoints
- [ ] Lifespan events setup for init_db and close_db
- [ ] Tests override session dependency
- [ ] No lazy loading (all relationships eager loaded)

---

## Summary

FastAPI integration with async SQLModel:
1. **Create session dependency** with error handling
2. **Use in all endpoints** as parameter
3. **Eager load relationships** before returning
4. **Catch database errors** and return appropriate HTTP status
5. **Use response models** to prevent circular dependencies
6. **Implement pagination** for list endpoints
7. **Setup lifespan events** for startup/shutdown
8. **Override dependency in tests** for testing
