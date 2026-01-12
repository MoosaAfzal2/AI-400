# ServiceBase Pattern - Generic CRUD Service Layer

Master the ServiceBase (formerly CRUDBase) pattern for building reusable, type-safe CRUD services with eager loading support, filtering, sorting, and transaction management.

**Cross-Skill References**: See **fastapi-builder skill** for integrating ServiceBase into endpoints; see **pytest-testing skill** `fastapi-sqlmodel-testing.md` for testing ServiceBase operations.

## Why ServiceBase?

The ServiceBase pattern provides:
- **Reusable CRUD operations** - get, create, update, delete with common patterns
- **Type safety** - Generic[ModelType, CreateSchemaType, UpdateSchemaType]
- **Eager loading support** - load_options parameter for selectinload/joinedload
- **Advanced filtering** - Supports operators like gt, lt, gte, lte, ilike, in, between, etc.
- **Sorting & pagination** - Built-in offset/limit with customizable sort columns
- **Error handling** - IntegrityError handling with rollback
- **Transaction control** - Optional commit and multi-record operations

---

## ServiceBase Class Definition

### Full ServiceBase Implementation

```python
# src/crud/service_base.py

from typing import (
    Any,
    Generic,
    TypeVar,
    Union,
    Optional,
    Callable,
    overload,
    Literal,
    List,
)
from uuid import UUID
from enum import Enum

from fastapi import HTTPException
from pydantic import BaseModel

from sqlmodel import (
    SQLModel,
    select,
    update,
    delete,
    func,
    or_,
)
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlalchemy import exc
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.exc import MultipleResultsFound


class OrderEnum(str, Enum):
    asc = "asc"
    desc = "desc"


ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
T = TypeVar("T", bound=SQLModel)
ID_TYPES = TypeVar("ID_TYPES", str, int, UUID)


class ServiceBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic service base class for CRUD operations on SQLModel.

    Supports eager loading with load_options (selectinload/joinedload),
    advanced filtering, sorting, and transaction management.

    Usage:
        class UserService(ServiceBase[User, UserCreate, UserUpdate]):
            pass

        user_service = UserService(User)
        user = await user_service.get(db=session, id=1, load_options=[...])
    """

    # Supported filter operators for advanced querying
    _SUPPORTED_FILTERS = {
        "gt": lambda column: column.__gt__,      # Greater than
        "lt": lambda column: column.__lt__,      # Less than
        "gte": lambda column: column.__ge__,     # Greater than or equal
        "lte": lambda column: column.__le__,     # Less than or equal
        "ne": lambda column: column.__ne__,      # Not equal
        "is": lambda column: column.is_,         # IS NULL check
        "is_not": lambda column: column.is_not,  # IS NOT NULL check
        "like": lambda column: column.like,      # SQL LIKE
        "notlike": lambda column: column.notlike,# SQL NOT LIKE
        "ilike": lambda column: column.ilike,    # Case-insensitive LIKE
        "notilike": lambda column: column.notilike,  # Case-insensitive NOT LIKE
        "startswith": lambda column: column.startswith,  # String starts with
        "endswith": lambda column: column.endswith,      # String ends with
        "contains": lambda column: column.contains,      # String contains
        "match": lambda column: column.match,    # Full-text match
        "between": lambda column: column.between,# Between range
        "in": lambda column: column.in_,        # IN list
        "not_in": lambda column: column.not_in, # NOT IN list
    }

    def __init__(self, model: type[ModelType]) -> None:
        """
        Initialize service with model class.

        Args:
            model: SQLModel class to operate on
        """
        self.model = model
        self.model_col_names = [col.key for col in model.__table__.columns]  # type: ignore

    def _get_sqlalchemy_filter(
        self,
        operator: str,
        value: Any,
    ) -> Optional[Callable[[str], Callable]]:
        """Get SQLAlchemy filter operator function."""
        if operator in {"in", "not_in", "between"}:
            if not isinstance(value, (tuple, list, set)):
                raise ValueError(f"<{operator}> filter must be tuple, list or set")
        return self._SUPPORTED_FILTERS.get(operator)

    def _parse_filters(
        self, model: Optional[Union[type[ModelType], AliasedClass]] = None, **kwargs
    ) -> list[ColumnElement]:
        """
        Parse filter kwargs into SQLAlchemy filter expressions.

        Supports:
            - Simple: id=1 → column == 1
            - Operators: id__gt=5 → column > 5
            - OR filters: field__or={"gt": 5, "lt": 10}
        """
        model = model or self.model
        filters = []

        for key, value in kwargs.items():
            if "__" in key:
                field_name, op = key.rsplit("__", 1)
                column = getattr(model, field_name, None)
                if column is None:
                    raise ValueError(f"Invalid filter column: {field_name}")
                if op == "or":
                    or_filters = [
                        sqlalchemy_filter(column)(or_value)
                        for or_key, or_value in value.items()
                        if (
                            sqlalchemy_filter := self._get_sqlalchemy_filter(
                                or_key, value
                            )
                        )
                        is not None
                    ]
                    filters.append(or_(*or_filters))
                else:
                    sqlalchemy_filter = self._get_sqlalchemy_filter(op, value)
                    if sqlalchemy_filter:
                        filters.append(sqlalchemy_filter(column)(value))
            else:
                column = getattr(model, key, None)
                if column is not None:
                    filters.append(column == value)

        return filters

    # ========================================================================
    # READ OPERATIONS
    # ========================================================================

    async def get(
        self, *, db: AsyncSession, load_options: Optional[list[Any]] = None, **kwargs
    ) -> Union[ModelType, None]:
        """
        Get single record with optional eager loading.

        Args:
            db: AsyncSession for database access
            load_options: List of selectinload/joinedload options
            **kwargs: Filter criteria (id=1, email='test@example.com', etc.)

        Returns:
            Model instance or None

        Example:
            from sqlalchemy.orm import selectinload
            user = await user_service.get(
                db=session,
                id=1,
                load_options=[selectinload(User.profile)]
            )
        """
        filters = self._parse_filters(**kwargs)
        query = select(self.model).filter(*filters)
        if load_options:
            for option in load_options:
                query = query.options(option)
        response = await db.exec(query)
        return response.one_or_none()

    async def get_by_ids(
        self,
        *,
        db: AsyncSession,
        list_ids: list[ID_TYPES],
        load_options: Optional[list[Any]] = None,
        **kwargs,
    ) -> list[ModelType]:
        """
        Get multiple records by ID list with optional filters.

        Args:
            db: AsyncSession for database access
            list_ids: List of IDs to fetch
            load_options: List of selectinload/joinedload options
            **kwargs: Additional filter criteria

        Returns:
            List of model instances

        Example:
            users = await user_service.get_by_ids(
                db=session,
                list_ids=[1, 2, 3],
                load_options=[selectinload(User.posts)]
            )
        """
        filters = self._parse_filters(**kwargs)
        query = select(self.model).where(self.model.id.in_(list_ids)).filter(*filters)  # type: ignore
        if load_options:
            for option in load_options:
                query = query.options(option)
        response = await db.exec(query)
        return list(response.all())

    async def get_multi(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        db: AsyncSession,
        sort_columns: Optional[Union[str, list[str]]] = None,
        sort_orders: Optional[Union[str, list[str]]] = None,
        load_options: Optional[list[Any]] = None,
        **kwargs,
    ) -> list[ModelType]:
        """
        Get paginated records with optional sorting and eager loading.

        Args:
            offset: Number of records to skip
            limit: Maximum records to return
            db: AsyncSession for database access
            sort_columns: Column(s) to sort by
            sort_orders: Sort order(s) ("asc" or "desc")
            load_options: List of selectinload/joinedload options
            **kwargs: Filter criteria

        Returns:
            List of model instances

        Example:
            users = await user_service.get_multi(
                db=session,
                offset=0,
                limit=20,
                sort_columns="created_at",
                sort_orders="desc",
                is_active=True,
                load_options=[selectinload(User.posts)]
            )
        """
        filters = self._parse_filters(**kwargs)
        query = select(self.model).offset(offset).limit(limit).filter(*filters)

        if load_options:
            for option in load_options:
                query = query.options(option)

        # Handle sorting
        if sort_columns:
            if isinstance(sort_columns, str):
                sort_columns = [sort_columns]
            if not sort_orders:
                sort_orders = ["asc"] * len(sort_columns)

            for col, order in zip(sort_columns, sort_orders):
                column = getattr(self.model, col)
                if order.lower() == "desc":
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())

        response = await db.exec(query)
        return list(response.all())

    async def get_multi_ordered(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: str = "id",
        order: OrderEnum = OrderEnum.asc,
        db: AsyncSession,
        load_options: Optional[list[Any]] = None,
        **kwargs,
    ) -> list[ModelType]:
        """
        Get paginated records with single column sorting and eager loading.

        Args:
            offset: Number of records to skip
            limit: Maximum records to return
            order_by: Column to sort by (defaults to "id")
            order: Sort order (asc or desc)
            db: AsyncSession for database access
            load_options: List of selectinload/joinedload options
            **kwargs: Filter criteria

        Returns:
            List of model instances
        """
        columns = self.model.__table__.columns  # type: ignore

        if order_by not in columns:
            order_by = "id"

        filters = self._parse_filters(**kwargs)
        if order == OrderEnum.asc:
            query = (
                select(self.model)
                .offset(offset)
                .limit(limit)
                .order_by(columns[order_by].asc())
                .filter(*filters,)
            )
        else:
            query = (
                select(self.model)
                .offset(offset)
                .limit(limit)
                .order_by(columns[order_by].desc())
                .filter(*filters,)
            )

        if load_options:
            for option in load_options:
                query = query.options(option)

        response = await db.exec(query)
        return list(response.all())

    async def count(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> int:
        """
        Count records matching filters.

        Args:
            db: AsyncSession for database access
            **kwargs: Filter criteria

        Returns:
            Count of matching records

        Example:
            total = await user_service.count(db=session, is_active=True)
        """
        filters = self._parse_filters(**kwargs)
        query = select(func.count()).select_from(
            select(self.model).filter(*filters).subquery()
        )
        response = await db.exec(query)
        return response.one()

    # ========================================================================
    # CREATE OPERATIONS
    # ========================================================================

    async def create(
        self,
        *,
        db: AsyncSession,
        object: CreateSchemaType,
        commit: Optional[bool] = True,
    ) -> ModelType:
        """
        Create single record.

        Args:
            db: AsyncSession for database access
            object: Pydantic schema with creation data
            commit: Whether to commit transaction

        Returns:
            Created model instance

        Raises:
            HTTPException: If IntegrityError (409 Conflict)

        Example:
            user = await user_service.create(
                db=session,
                object=UserCreate(email='test@example.com', name='John')
            )
        """
        object_dict = object.model_dump()
        db_object: ModelType = self.model(**object_dict)
        try:
            db.add(db_object)
            if commit:
                await db.commit()
                await db.refresh(db_object)
        except exc.IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Resource already exists",
            )
        return db_object

    async def create_multi(
        self,
        *,
        db: AsyncSession,
        objects: list[CreateSchemaType],
        commit: Optional[bool] = True,
    ) -> list[ModelType]:
        """
        Create multiple records in single transaction.

        Args:
            db: AsyncSession for database access
            objects: List of Pydantic schemas
            commit: Whether to commit transaction

        Returns:
            List of created model instances

        Example:
            users = await user_service.create_multi(
                db=session,
                objects=[
                    UserCreate(email='user1@example.com', name='User 1'),
                    UserCreate(email='user2@example.com', name='User 2'),
                ]
            )
        """
        db_objects = []
        for object in objects:
            db_object = await self.create(db=db, object=object, commit=False)
            db_objects.append(db_object)

        if commit:
            await db.commit()
            for obj in db_objects:
                await db.refresh(obj)

        return db_objects

    # ========================================================================
    # UPDATE OPERATIONS
    # ========================================================================

    @overload
    async def update(
        self,
        db: AsyncSession,
        object: UpdateSchemaType,
        allow_multiple: Literal[False] = False,
        commit: bool = True,
        return_updated: bool = False,
        **kwargs: Any,
    ) -> Optional[ModelType]: ...

    @overload
    async def update(
        self,
        db: AsyncSession,
        object: UpdateSchemaType,
        allow_multiple: Literal[True],
        commit: bool = True,
        return_updated: bool = False,
        **kwargs: Any,
    ) -> List[ModelType]: ...

    async def update(
        self,
        db: AsyncSession,
        object: UpdateSchemaType,
        allow_multiple: bool = False,
        commit: bool = True,
        return_updated: bool = False,
        **kwargs: Any,
    ) -> Union[ModelType, List[ModelType], None]:
        """
        Update one or more records.

        Args:
            db: AsyncSession for database access
            object: Pydantic schema with update data
            allow_multiple: Whether to allow multiple records update
            commit: Whether to commit transaction
            return_updated: Whether to return updated records
            **kwargs: Filter criteria for which records to update

        Returns:
            Updated model instance(s) or None

        Raises:
            MultipleResultsFound: If allow_multiple=False and multiple records match

        Example:
            # Update single user
            user = await user_service.update(
                db=session,
                object=UserUpdate(name='New Name'),
                id=1,
                return_updated=True
            )

            # Update multiple users
            users = await user_service.update(
                db=session,
                object=UserUpdate(is_active=False),
                allow_multiple=True,
                role='inactive',
                return_updated=True
            )
        """
        if not allow_multiple and (total_count := await self.count(db, **kwargs)) > 1:
            raise MultipleResultsFound(
                f"Expected exactly one record to update, found {total_count}."
            )

        update_data = object.model_dump(exclude_unset=True)
        filters = self._parse_filters(**kwargs)
        stmt = update(self.model).filter(*filters).values(update_data)
        await db.execute(stmt)

        if commit:
            await db.commit()

        db_objects = None

        if return_updated:
            results = await db.execute(select(self.model).filter(*filters))
            if allow_multiple:
                db_objects = list(results.scalars().all())
            else:
                db_objects = results.scalars().one_or_none()  # type: ignore

        return db_objects

    # ========================================================================
    # DELETE OPERATIONS
    # ========================================================================

    async def delete(
        self,
        db: AsyncSession,
        allow_multiple: bool = False,
        commit: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Delete one or more records.

        Args:
            db: AsyncSession for database access
            allow_multiple: Whether to allow multiple records delete
            commit: Whether to commit transaction
            **kwargs: Filter criteria for which records to delete

        Raises:
            MultipleResultsFound: If allow_multiple=False and multiple records match

        Example:
            # Delete single user
            await user_service.delete(db=session, id=1)

            # Delete multiple inactive users
            await user_service.delete(
                db=session,
                allow_multiple=True,
                is_active=False
            )
        """
        if not allow_multiple and (total_count := await self.count(db, **kwargs)) > 1:
            raise MultipleResultsFound(
                f"Expected exactly one record to delete, found {total_count}."
            )

        filters = self._parse_filters(**kwargs)
        stmt = delete(self.model).filter(*filters)
        await db.exec(stmt)  # type: ignore
        if commit:
            await db.commit()
```

---

## Creating Model-Specific Services

### UserService Example

```python
# src/crud/user_service.py

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import User, UserCreate, UserUpdate
from src.crud.service_base import ServiceBase


class UserService(ServiceBase[User, UserCreate, UserUpdate]):
    """
    User-specific service extending ServiceBase.
    Can add custom methods beyond standard CRUD.
    """

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Get user by email with eager-loaded profile."""
        return await self.get(
            db=db,
            email=email,
            load_options=[selectinload(User.profile)]
        )

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> User | None:
        """Authenticate user by email and password."""
        user = await self.get(db=db, email=email)
        if user and user.verify_password(password):
            return user
        return None


# Create singleton instance
user_service = UserService(User)
```

### TeamService Example

```python
# src/crud/team_service.py

from sqlalchemy.orm import selectinload

from src.models import Team, TeamCreate, TeamUpdate
from src.crud.service_base import ServiceBase


class TeamService(ServiceBase[Team, TeamCreate, TeamUpdate]):
    """Team-specific service extending ServiceBase."""

    async def get_with_members(self, db, team_id: int) -> Team | None:
        """Get team with all members eagerly loaded."""
        return await self.get(
            db=db,
            id=team_id,
            load_options=[selectinload(Team.members)]
        )


team_service = TeamService(Team)
```

### JobService Example

```python
# src/crud/job_service.py

from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Job, JobCreate, JobUpdate, IJobStatusEnum
from src.crud.service_base import ServiceBase


class JobService(ServiceBase[Job, JobCreate, JobUpdate]):
    """Job-specific service with custom status management."""

    async def change_status(
        self,
        db: AsyncSession,
        new_status: IJobStatusEnum,
        allow_multiple: bool = False,
        return_updated: bool = False,
        **kwargs
    ) -> Job | list[Job] | None:
        """Change job status with optional return of updated records."""
        return await self.update(
            db=db,
            object=JobUpdate(status=new_status),
            allow_multiple=allow_multiple,
            return_updated=return_updated,
            **kwargs
        )

    async def get_with_proposals(self, db: AsyncSession, job_id: int) -> Job | None:
        """Get job with all proposals eagerly loaded."""
        return await self.get(
            db=db,
            id=job_id,
            load_options=[selectinload(Job.proposals)]
        )


job_service = JobService(Job)
```

---

## Integration with FastAPI Endpoints

### Dependency Injection

```python
# src/api/deps.py

from typing import Annotated
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.crud.user_service import user_service
from src.crud.team_service import team_service
from src.crud.job_service import job_service


# Service dependencies
UserServiceDep = Annotated[type[user_service.__class__], Depends(lambda: user_service)]
TeamServiceDep = Annotated[type[team_service.__class__], Depends(lambda: team_service)]
JobServiceDep = Annotated[type[job_service.__class__], Depends(lambda: job_service)]
```

### Using ServiceBase in Endpoints

```python
# src/api/v1/routes/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload

from src.api.deps import UserServiceDep, AsyncSessionDep
from src.models import User, UserCreate, UserUpdate
from src.crud.user_service import user_service


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSessionDep,
):
    """Create new user."""
    user = await user_service.create(db=db, object=user_in)
    return {"id": user.id, "email": user.email}


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    db: AsyncSessionDep,
):
    """Get user with profile."""
    user = await user_service.get(
        db=db,
        id=user_id,
        load_options=[selectinload(User.profile)]
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/", response_model=dict)
async def list_users(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSessionDep,
):
    """List users with pagination."""
    users = await user_service.get_multi(
        db=db,
        offset=skip,
        limit=limit,
        load_options=[selectinload(User.profile)]
    )
    total = await user_service.count(db=db)
    return {
        "items": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSessionDep,
):
    """Update user."""
    user = await user_service.update(
        db=db,
        object=user_in,
        id=user_id,
        return_updated=True
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSessionDep,
):
    """Delete user."""
    user = await user_service.get(db=db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    await user_service.delete(db=db, id=user_id)
```

---

## Advanced Filtering Examples

### Simple Equality Filters

```python
# Filter by single field
user = await user_service.get(db=session, email="test@example.com")

# Filter by multiple fields
users = await user_service.get_multi(
    db=session,
    is_active=True,
    role="admin"
)
```

### Operator Filters

```python
# Greater than / less than
high_salary_users = await user_service.get_multi(
    db=session,
    salary__gte=50000,
    salary__lte=100000
)

# String filters
users = await user_service.get_multi(
    db=session,
    email__ilike="%@example.com"  # Case-insensitive contains
)

# Between
recent_users = await user_service.get_multi(
    db=session,
    created_at__between=(start_date, end_date)
)

# IN list
users = await user_service.get_multi(
    db=session,
    status__in=["active", "pending"]
)
```

### OR Filters

```python
# Match any condition
users = await user_service.get_multi(
    db=session,
    email__or={
        "ilike": "%@example.com",
        "ilike": "%@test.com"
    }
)
```

---

## Testing ServiceBase Operations

### Unit Tests with Fixtures

```python
# tests/conftest.py

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from src.crud.user_service import user_service


@pytest_asyncio.fixture
async def test_engine():
    """Create in-memory test database."""
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
    """Create test async session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
```

### Testing CRUD Operations

```python
# tests/unit/test_user_service.py

import pytest
from sqlalchemy.orm import selectinload

from src.models import User, UserCreate, UserUpdate
from src.crud.user_service import user_service


@pytest.mark.asyncio
async def test_create_user(test_session):
    """Test creating user."""
    user_in = UserCreate(email="test@example.com", name="Test User")
    user = await user_service.create(db=test_session, object=user_in)

    assert user.id is not None
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_with_eager_loading(test_session):
    """Test getting user with eager-loaded profile."""
    # Create user with profile
    user_in = UserCreate(email="test@example.com", name="Test User")
    user = await user_service.create(db=test_session, object=user_in)

    # Fetch with eager loading
    fetched = await user_service.get(
        db=test_session,
        id=user.id,
        load_options=[selectinload(User.profile)]
    )

    assert fetched is not None
    assert fetched.profile is not None


@pytest.mark.asyncio
async def test_get_multi_with_filtering(test_session):
    """Test getting multiple records with filters."""
    # Create test users
    users_in = [
        UserCreate(email="user1@example.com", name="User 1"),
        UserCreate(email="user2@example.com", name="User 2"),
    ]
    for u in users_in:
        await user_service.create(db=test_session, object=u)

    # Fetch with filter
    users = await user_service.get_multi(
        db=test_session,
        email__ilike="%example.com"
    )

    assert len(users) == 2


@pytest.mark.asyncio
async def test_update_user(test_session):
    """Test updating user."""
    # Create user
    user_in = UserCreate(email="test@example.com", name="Test User")
    user = await user_service.create(db=test_session, object=user_in)

    # Update
    update_in = UserUpdate(name="Updated Name")
    updated = await user_service.update(
        db=test_session,
        object=update_in,
        id=user.id,
        return_updated=True
    )

    assert updated.name == "Updated Name"


@pytest.mark.asyncio
async def test_delete_user(test_session):
    """Test deleting user."""
    # Create and delete
    user_in = UserCreate(email="test@example.com", name="Test User")
    user = await user_service.create(db=test_session, object=user_in)

    await user_service.delete(db=test_session, id=user.id)

    # Verify deleted
    deleted = await user_service.get(db=test_session, id=user.id)
    assert deleted is None
```

---

## ServiceBase Best Practices

### ✅ Do

- **Use load_options for eager loading** - Always load relationships to avoid lazy loading errors
- **Create model-specific services** - Inherit from ServiceBase for custom behavior
- **Use type hints** - Generic[ModelType, CreateSchemaType, UpdateSchemaType]
- **Handle IntegrityError** - Catch constraint violations (duplicates, foreign keys)
- **Test with fixtures** - Use in-memory database for fast, isolated tests
- **Use filtering operators** - Leverage gt, lt, ilike, in, between for advanced queries
- **Respect transactions** - Use commit=False for batch operations

### ❌ Don't

- **Access relationships without eager loading** - Will raise error in async
- **Forget to await** - All ServiceBase methods are async
- **Mix sync and async** - Use AsyncSession, not Session
- **Hardcode limit values** - Make pagination configurable
- **Skip error handling** - IntegrityError needs explicit handling
- **Create service instances per request** - Use singleton services

---

## ServiceBase Checklist

Before using ServiceBase in production:

- [ ] ServiceBase initialized with correct model types
- [ ] All model-specific services inherit from ServiceBase
- [ ] Relationships use eager loading (selectinload/joinedload)
- [ ] No lazy loading in async code
- [ ] Error handling for IntegrityError
- [ ] Pagination implemented for list endpoints
- [ ] Filter operators tested (gt, lt, ilike, in, etc.)
- [ ] Custom methods added to model-specific services
- [ ] Tests cover CRUD operations
- [ ] Tests verify eager loading
- [ ] Dependency injection configured
- [ ] Endpoints use service layer correctly

---

## Summary

ServiceBase Pattern Best Practices:

1. **Define ServiceBase** with Generic[ModelType, CreateSchemaType, UpdateSchemaType]
2. **Create model-specific services** inheriting from ServiceBase
3. **Use load_options** for all eager loading (selectinload/joinedload)
4. **Leverage filtering** with operators (gt, lt, ilike, in, between)
5. **Handle transactions** with commit parameter
6. **Integrate with FastAPI** via dependency injection
7. **Test thoroughly** with pytest-asyncio and fixtures
8. **Use singleton instances** for each service
