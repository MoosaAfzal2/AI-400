# Async CRUD Operations - SQLModel Patterns

Implement async create, read, update, and delete operations using SQLModel with proper async/await patterns, transactions, and error handling.

## Async Create Operations

### Simple Insert

```python
# src/services/user.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.models import User

async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
) -> User:
    """Create and return new user"""
    # Create model instance
    user = User(username=username, email=email)

    # Add to session
    session.add(user)

    # Flush to get ID (doesn't commit)
    await session.flush()

    # Commit changes
    await session.commit()

    # Refresh to reload from database
    await session.refresh(user)

    return user
```

### Bulk Insert

```python
async def create_users_bulk(
    session: AsyncSession,
    users_data: List[Dict[str, str]],
) -> List[User]:
    """Create multiple users at once"""
    users = [User(**data) for data in users_data]

    # Add all users
    session.add_all(users)

    # Flush to get IDs
    await session.flush()

    # Commit
    await session.commit()

    # Refresh all
    for user in users:
        await session.refresh(user)

    return users
```

---

## Async Read Operations

### Get by ID

```python
async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> Optional[User]:
    """Get user by ID"""
    user = await session.get(User, user_id)
    return user
```

### Get with Filter

```python
async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> Optional[User]:
    """Get user by username"""
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    return result.scalar_one_or_none()
```

### Get Many with Pagination

```python
from typing import List

async def get_users_paginated(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 10,
) -> tuple[List[User], int]:
    """Get paginated list of users with total count"""
    # Get total count
    count_statement = select(func.count(User.id))
    count_result = await session.execute(count_statement)
    total = count_result.scalar()

    # Get paginated results
    statement = select(User).offset(skip).limit(limit)
    result = await session.execute(statement)
    users = result.scalars().all()

    return users, total
```

### Complex Filtering

```python
from sqlalchemy import and_, or_

async def search_users(
    session: AsyncSession,
    username: Optional[str] = None,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> List[User]:
    """Search users with multiple filters"""
    statement = select(User)

    filters = []
    if username:
        filters.append(User.username.ilike(f"%{username}%"))
    if email:
        filters.append(User.email == email)
    if is_active is not None:
        filters.append(User.is_active == is_active)

    if filters:
        statement = statement.where(and_(*filters))

    result = await session.execute(statement)
    return result.scalars().all()
```

---

## Async Update Operations

### Update Single Field

```python
async def update_user_username(
    session: AsyncSession,
    user_id: int,
    new_username: str,
) -> Optional[User]:
    """Update user's username"""
    user = await session.get(User, user_id)
    if not user:
        return None

    user.username = new_username
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user
```

### Update Multiple Fields

```python
async def update_user(
    session: AsyncSession,
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
) -> Optional[User]:
    """Update user with multiple fields"""
    user = await session.get(User, user_id)
    if not user:
        return None

    # Update only provided fields
    if username is not None:
        user.username = username
    if email is not None:
        user.email = email
    if full_name is not None:
        user.full_name = full_name

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user
```

### Bulk Update

```python
from sqlalchemy import update

async def update_users_bulk(
    session: AsyncSession,
    user_ids: List[int],
    is_active: bool,
) -> int:
    """Update multiple users (returns count updated)"""
    statement = (
        update(User)
        .where(User.id.in_(user_ids))
        .values(is_active=is_active)
    )
    result = await session.execute(statement)
    await session.commit()
    return result.rowcount
```

---

## Async Delete Operations

### Delete by ID

```python
async def delete_user(
    session: AsyncSession,
    user_id: int,
) -> bool:
    """Delete user by ID"""
    user = await session.get(User, user_id)
    if not user:
        return False

    await session.delete(user)
    await session.commit()
    return True
```

### Bulk Delete

```python
from sqlalchemy import delete

async def delete_users_bulk(
    session: AsyncSession,
    user_ids: List[int],
) -> int:
    """Delete multiple users (returns count deleted)"""
    statement = delete(User).where(User.id.in_(user_ids))
    result = await session.execute(statement)
    await session.commit()
    return result.rowcount
```

---

## Eager Loading for Relationships

### selectinload (Recommended)

```python
from sqlalchemy.orm import selectinload

async def get_team_with_members(
    session: AsyncSession,
    team_id: int,
) -> Optional[Team]:
    """Get team with all members loaded"""
    statement = (
        select(Team)
        .where(Team.id == team_id)
        .options(selectinload(Team.members))
    )
    result = await session.execute(statement)
    return result.unique().scalar_one_or_none()
```

### joinedload (For Single Objects)

```python
from sqlalchemy.orm import joinedload

async def get_user_with_team(
    session: AsyncSession,
    user_id: int,
) -> Optional[User]:
    """Get user with team (single object)"""
    statement = (
        select(User)
        .where(User.id == user_id)
        .options(joinedload(User.team))
    )
    result = await session.execute(statement)
    return result.unique().scalar_one_or_none()
```

### Multiple Relationships

```python
async def get_user_full(
    session: AsyncSession,
    user_id: int,
) -> Optional[User]:
    """Get user with team and posts"""
    statement = (
        select(User)
        .where(User.id == user_id)
        .options(
            joinedload(User.team),
            selectinload(User.posts),
        )
    )
    result = await session.execute(statement)
    return result.unique().scalar_one_or_none()
```

---

## Transactions

### Manual Transaction Control

```python
async def transfer_credits(
    session: AsyncSession,
    from_user_id: int,
    to_user_id: int,
    amount: float,
) -> bool:
    """Transfer credits between users (atomic operation)"""
    try:
        # Start transaction (implicit)
        from_user = await session.get(User, from_user_id)
        to_user = await session.get(User, to_user_id)

        if not from_user or not to_user:
            raise ValueError("User not found")

        if from_user.credits < amount:
            raise ValueError("Insufficient credits")

        # Perform operations
        from_user.credits -= amount
        to_user.credits += amount

        session.add(from_user)
        session.add(to_user)

        # Commit atomically
        await session.commit()
        return True

    except Exception as e:
        # Rollback on any error
        await session.rollback()
        raise e
```

### Savepoints (Nested Transactions)

```python
async def complex_operation(session: AsyncSession) -> None:
    """Operation with savepoints"""
    try:
        # Create savepoint
        savepoint = await session.begin_nested()

        # Do work
        user = User(username="test")
        session.add(user)
        await session.flush()

        # If error, rollback to savepoint only
        try:
            # More operations
            pass
        except Exception:
            await savepoint.rollback()

        # Commit all
        await session.commit()

    except Exception:
        await session.rollback()
        raise
```

---

## Error Handling

### Integrity Errors

```python
from sqlalchemy.exc import IntegrityError

async def create_user_safe(
    session: AsyncSession,
    username: str,
    email: str,
) -> tuple[Optional[User], Optional[str]]:
    """Create user with error handling"""
    try:
        user = User(username=username, email=email)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user, None

    except IntegrityError as e:
        await session.rollback()
        if "username" in str(e):
            return None, "Username already exists"
        elif "email" in str(e):
            return None, "Email already exists"
        else:
            return None, "Duplicate entry"

    except Exception as e:
        await session.rollback()
        return None, f"Database error: {str(e)}"
```

### Validation Errors

```python
from pydantic import ValidationError

async def create_user_validated(
    session: AsyncSession,
    data: dict,
) -> tuple[Optional[User], Optional[str]]:
    """Create user with validation"""
    try:
        user = User(**data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user, None

    except ValidationError as e:
        return None, f"Validation error: {str(e)}"

    except IntegrityError:
        await session.rollback()
        return None, "Duplicate entry"

    except Exception as e:
        await session.rollback()
        return None, f"Database error: {str(e)}"
```

---

## Batch Operations

### Batch Insert with Progress

```python
from typing import AsyncIterator

async def insert_large_dataset(
    session: AsyncSession,
    data: List[dict],
    batch_size: int = 1000,
) -> int:
    """Insert large dataset in batches"""
    total = 0

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        users = [User(**item) for item in batch]

        session.add_all(users)
        await session.flush()
        total += len(batch)

        print(f"Inserted {total} records")

    await session.commit()
    return total
```

### Stream Results (Memory Efficient)

```python
async def process_all_users(
    session: AsyncSession,
) -> AsyncIterator[User]:
    """Process users one at a time (memory efficient)"""
    statement = select(User)
    result = await session.stream(statement)

    async for user in result.scalars():
        yield user
```

---

## Performance Optimization

### Avoid N+1 Queries

```python
# ❌ BAD - N+1 problem (1 query for users + N queries for teams)
async def get_users_bad(session: AsyncSession):
    statement = select(User)
    result = await session.execute(statement)
    users = result.scalars().all()

    # This causes N additional queries!
    for user in users:
        print(user.team.name)  # Lazy load each time

# ✅ GOOD - Use joinedload or selectinload
async def get_users_good(session: AsyncSession):
    statement = (
        select(User)
        .options(joinedload(User.team))
    )
    result = await session.execute(statement)
    users = result.unique().scalars().all()

    # No additional queries
    for user in users:
        print(user.team.name)
```

### Connection Pooling with Proper Cleanup

```python
async def get_or_create_user(
    session: AsyncSession,
    username: str,
    email: str,
) -> User:
    """Get existing or create new user"""
    # Try to get
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if user:
        return user

    # Create if not exists
    user = User(username=username, email=email)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

---

## Testing Async Operations

```python
import pytest

@pytest.mark.asyncio
async def test_create_user(test_session):
    """Test user creation"""
    user = await create_user(test_session, "john", "john@example.com")
    assert user.id is not None
    assert user.username == "john"

@pytest.mark.asyncio
async def test_duplicate_username(test_session):
    """Test duplicate username error"""
    await create_user(test_session, "john", "john@example.com")

    user, error = await create_user_safe(
        test_session, "john", "john2@example.com"
    )
    assert user is None
    assert error is not None
```

---

## Async Operations Checklist

Before production:

- [ ] All database operations are async (await everywhere)
- [ ] Relationships use eager loading (selectinload/joinedload)
- [ ] Error handling with proper rollback
- [ ] Transactions used for multi-step operations
- [ ] No N+1 query problems
- [ ] Batch operations for large datasets
- [ ] Connection pool configured correctly
- [ ] Tests verify async patterns work
- [ ] Response models exclude sensitive fields
- [ ] Pagination implemented for list endpoints

---

## Summary

Async CRUD operations require:
1. **Async/await** on all database calls
2. **Eager loading** with selectinload/joinedload for relationships
3. **Error handling** with rollback on exceptions
4. **Transactions** for multi-step operations
5. **Connection cleanup** after operations
6. **Batch processing** for large datasets
