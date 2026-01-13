"""Todo service for CRUD operations."""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..exceptions import ResourceNotFoundException
from ..models import Todo


class TodoService:
    """Service for todo-related database operations.

    Provides async CRUD operations for todos with user-based filtering
    to ensure data isolation and privacy.
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: AsyncSession for database operations
        """
        self.session = session

    async def create_todo(
        self,
        user_id: int,
        title: str,
        description: Optional[str] = None,
    ) -> Todo:
        """Create new todo for user.

        Args:
            user_id: Owner user ID
            title: Todo title
            description: Optional todo description

        Returns:
            Created Todo

        Raises:
            IntegrityError: If database constraint violated
        """
        todo = Todo(
            user_id=user_id,
            title=title,
            description=description,
            is_completed=False,
        )

        try:
            self.session.add(todo)
            await self.session.flush()  # Get the ID without committing
            return todo
        except IntegrityError as exc:
            await self.session.rollback()
            raise

    async def get_todo(self, todo_id: int, user_id: int) -> Optional[Todo]:
        """Get todo by ID with user isolation.

        Args:
            todo_id: Todo ID
            user_id: Owner user ID (for authorization)

        Returns:
            Todo or None if not found or user doesn't own it
        """
        statement = select(Todo).where(
            (Todo.id == todo_id) & (Todo.user_id == user_id)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def list_todos(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        is_completed: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Todo], int]:
        """List todos for user with pagination and filtering.

        Args:
            user_id: Owner user ID
            skip: Number of items to skip
            limit: Number of items to return
            is_completed: Filter by completion status (optional)
            sort_by: Field to sort by (created_at, updated_at, title)
            sort_order: Sort order (asc, desc)

        Returns:
            Tuple of (todos list, total count)
        """
        # Build base query
        statement = select(Todo).where(Todo.user_id == user_id)

        # Apply filters
        if is_completed is not None:
            statement = statement.where(Todo.is_completed == is_completed)

        # Get total count
        count_statement = select(Todo).where(Todo.user_id == user_id)
        if is_completed is not None:
            count_statement = count_statement.where(
                Todo.is_completed == is_completed
            )
        count_result = await self.session.execute(count_statement)
        total = len(count_result.scalars().all())

        # Apply sorting
        sort_field = getattr(Todo, sort_by, Todo.created_at)
        if sort_order.lower() == "asc":
            statement = statement.order_by(sort_field.asc())
        else:
            statement = statement.order_by(sort_field.desc())

        # Apply pagination
        statement = statement.offset(skip).limit(limit)

        result = await self.session.execute(statement)
        todos = result.scalars().all()

        return todos, total

    async def update_todo(
        self,
        todo_id: int,
        user_id: int,
        **kwargs,
    ) -> Todo:
        """Update todo fields with user isolation.

        Args:
            todo_id: Todo ID
            user_id: Owner user ID (for authorization)
            **kwargs: Fields to update (title, description, is_completed)

        Returns:
            Updated Todo

        Raises:
            ResourceNotFoundException: If todo not found or user doesn't own it
        """
        todo = await self.get_todo(todo_id, user_id)
        if not todo:
            raise ResourceNotFoundException(
                message="Todo not found",
                error_code="NOT_FOUND_002",
            )

        # Update fields
        for key, value in kwargs.items():
            if hasattr(todo, key) and key not in ("id", "user_id", "created_at"):
                setattr(todo, key, value)

        # If marking as completed, set completed_at timestamp
        if kwargs.get("is_completed") and not todo.completed_at:
            todo.completed_at = datetime.now(UTC).isoformat()

        # If marking as incomplete, clear completed_at
        if not kwargs.get("is_completed") and todo.completed_at:
            todo.completed_at = None

        self.session.add(todo)
        await self.session.flush()
        return todo

    async def delete_todo(self, todo_id: int, user_id: int) -> None:
        """Delete todo by ID with user isolation.

        Args:
            todo_id: Todo ID
            user_id: Owner user ID (for authorization)

        Raises:
            ResourceNotFoundException: If todo not found or user doesn't own it
        """
        todo = await self.get_todo(todo_id, user_id)
        if not todo:
            raise ResourceNotFoundException(
                message="Todo not found",
                error_code="NOT_FOUND_002",
            )

        await self.session.delete(todo)
        await self.session.flush()

    async def commit(self) -> None:
        """Commit transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        await self.session.rollback()
