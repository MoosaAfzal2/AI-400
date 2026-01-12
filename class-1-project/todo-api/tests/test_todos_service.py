"""Tests for todo service layer."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.todo_api.exceptions import ResourceNotFoundException
from src.todo_api.models import Todo
from src.todo_api.services import TodoService


class TestTodoService:
    """Test suite for TodoService."""

    async def test_create_todo(self, session: AsyncSession, test_user_id: int):
        """Test creating a new todo."""
        service = TodoService(session)

        todo = await service.create_todo(
            user_id=test_user_id,
            title="Buy groceries",
            description="Milk, eggs, bread",
        )

        assert todo.id is not None
        assert todo.user_id == test_user_id
        assert todo.title == "Buy groceries"
        assert todo.description == "Milk, eggs, bread"
        assert todo.is_completed is False
        assert todo.completed_at is None

    async def test_create_todo_minimal(self, session: AsyncSession, test_user_id: int):
        """Test creating a todo with minimal fields."""
        service = TodoService(session)

        todo = await service.create_todo(
            user_id=test_user_id,
            title="Task",
        )

        assert todo.id is not None
        assert todo.user_id == test_user_id
        assert todo.title == "Task"
        assert todo.description is None

    async def test_get_todo_by_id(self, session: AsyncSession, test_user_id: int):
        """Test retrieving a todo by ID."""
        service = TodoService(session)

        # Create todo
        created_todo = await service.create_todo(
            user_id=test_user_id,
            title="Test todo",
        )
        await service.commit()

        # Retrieve todo
        retrieved_todo = await service.get_todo(created_todo.id, test_user_id)

        assert retrieved_todo is not None
        assert retrieved_todo.id == created_todo.id
        assert retrieved_todo.title == "Test todo"

    async def test_get_todo_nonexistent(self, session: AsyncSession, test_user_id: int):
        """Test retrieving non-existent todo returns None."""
        service = TodoService(session)

        todo = await service.get_todo(9999, test_user_id)

        assert todo is None

    async def test_get_todo_user_isolation(
        self, session: AsyncSession, test_user_id: int, other_user_id: int
    ):
        """Test that users cannot access other users' todos."""
        service = TodoService(session)

        # Create todo for test_user
        created_todo = await service.create_todo(
            user_id=test_user_id,
            title="Private todo",
        )
        await service.commit()

        # Try to access with other user
        todo = await service.get_todo(created_todo.id, other_user_id)

        assert todo is None

    async def test_list_todos(self, session: AsyncSession, test_user_id: int):
        """Test listing todos with pagination."""
        service = TodoService(session)

        # Create multiple todos
        for i in range(5):
            await service.create_todo(
                user_id=test_user_id,
                title=f"Todo {i}",
            )
        await service.commit()

        # List todos
        todos, total = await service.list_todos(user_id=test_user_id, skip=0, limit=20)

        assert len(todos) == 5
        assert total == 5

    async def test_list_todos_pagination(self, session: AsyncSession, test_user_id: int):
        """Test pagination works correctly."""
        service = TodoService(session)

        # Create 25 todos
        for i in range(25):
            await service.create_todo(
                user_id=test_user_id,
                title=f"Todo {i}",
            )
        await service.commit()

        # First page
        todos_page1, total = await service.list_todos(
            user_id=test_user_id, skip=0, limit=10
        )
        assert len(todos_page1) == 10
        assert total == 25

        # Second page
        todos_page2, _ = await service.list_todos(
            user_id=test_user_id, skip=10, limit=10
        )
        assert len(todos_page2) == 10

        # Last page
        todos_page3, _ = await service.list_todos(
            user_id=test_user_id, skip=20, limit=10
        )
        assert len(todos_page3) == 5

    async def test_list_todos_filter_completed(
        self, session: AsyncSession, test_user_id: int
    ):
        """Test filtering todos by completion status."""
        service = TodoService(session)

        # Create completed and incomplete todos
        incomplete = await service.create_todo(
            user_id=test_user_id,
            title="Incomplete",
            description="Not done",
        )
        completed = await service.create_todo(
            user_id=test_user_id,
            title="Complete",
            description="Already done",
        )
        await service.commit()

        # Mark one as completed
        await service.update_todo(
            todo_id=completed.id,
            user_id=test_user_id,
            is_completed=True,
        )
        await service.commit()

        # Filter for incomplete
        incomplete_todos, total = await service.list_todos(
            user_id=test_user_id,
            is_completed=False,
        )
        assert len(incomplete_todos) == 1
        assert incomplete_todos[0].title == "Incomplete"

        # Filter for completed
        completed_todos, total = await service.list_todos(
            user_id=test_user_id,
            is_completed=True,
        )
        assert len(completed_todos) == 1
        assert completed_todos[0].title == "Complete"

    async def test_list_todos_sort_by_title(
        self, session: AsyncSession, test_user_id: int
    ):
        """Test sorting todos by title."""
        service = TodoService(session)

        # Create todos with different titles
        await service.create_todo(user_id=test_user_id, title="Zebra")
        await service.create_todo(user_id=test_user_id, title="Apple")
        await service.create_todo(user_id=test_user_id, title="Mango")
        await service.commit()

        # Sort ascending
        todos, _ = await service.list_todos(
            user_id=test_user_id,
            sort_by="title",
            sort_order="asc",
        )
        assert [t.title for t in todos] == ["Apple", "Mango", "Zebra"]

        # Sort descending
        todos, _ = await service.list_todos(
            user_id=test_user_id,
            sort_by="title",
            sort_order="desc",
        )
        assert [t.title for t in todos] == ["Zebra", "Mango", "Apple"]

    async def test_list_todos_user_isolation(
        self, session: AsyncSession, test_user_id: int, other_user_id: int
    ):
        """Test that users only see their own todos."""
        service = TodoService(session)

        # Create todos for both users
        await service.create_todo(user_id=test_user_id, title="User 1 todo")
        await service.create_todo(user_id=other_user_id, title="User 2 todo")
        await service.commit()

        # List todos for user 1
        todos1, total1 = await service.list_todos(user_id=test_user_id)
        assert len(todos1) == 1
        assert todos1[0].title == "User 1 todo"

        # List todos for user 2
        todos2, total2 = await service.list_todos(user_id=other_user_id)
        assert len(todos2) == 1
        assert todos2[0].title == "User 2 todo"

    async def test_update_todo_title(self, session: AsyncSession, test_user_id: int):
        """Test updating todo title."""
        service = TodoService(session)

        todo = await service.create_todo(
            user_id=test_user_id,
            title="Original",
        )
        await service.commit()

        updated = await service.update_todo(
            todo_id=todo.id,
            user_id=test_user_id,
            title="Updated",
        )
        await service.commit()

        assert updated.title == "Updated"

    async def test_update_todo_completion(
        self, session: AsyncSession, test_user_id: int
    ):
        """Test updating todo completion status."""
        service = TodoService(session)

        todo = await service.create_todo(
            user_id=test_user_id,
            title="Test",
        )
        assert todo.is_completed is False
        assert todo.completed_at is None
        await service.commit()

        # Mark as completed
        updated = await service.update_todo(
            todo_id=todo.id,
            user_id=test_user_id,
            is_completed=True,
        )
        assert updated.is_completed is True
        assert updated.completed_at is not None

        # Mark as incomplete
        updated = await service.update_todo(
            todo_id=todo.id,
            user_id=test_user_id,
            is_completed=False,
        )
        assert updated.is_completed is False
        assert updated.completed_at is None

    async def test_update_todo_nonexistent(
        self, session: AsyncSession, test_user_id: int
    ):
        """Test updating non-existent todo raises exception."""
        service = TodoService(session)

        with pytest.raises(ResourceNotFoundException):
            await service.update_todo(
                todo_id=9999,
                user_id=test_user_id,
                title="Updated",
            )

    async def test_update_todo_user_isolation(
        self, session: AsyncSession, test_user_id: int, other_user_id: int
    ):
        """Test that users cannot update other users' todos."""
        service = TodoService(session)

        # Create todo for test_user
        todo = await service.create_todo(
            user_id=test_user_id,
            title="Private",
        )
        await service.commit()

        # Try to update with other_user
        with pytest.raises(ResourceNotFoundException):
            await service.update_todo(
                todo_id=todo.id,
                user_id=other_user_id,
                title="Hacked",
            )

    async def test_delete_todo(self, session: AsyncSession, test_user_id: int):
        """Test deleting a todo."""
        service = TodoService(session)

        todo = await service.create_todo(
            user_id=test_user_id,
            title="To delete",
        )
        await service.commit()

        # Delete
        await service.delete_todo(todo_id=todo.id, user_id=test_user_id)
        await service.commit()

        # Verify deleted
        retrieved = await service.get_todo(todo.id, test_user_id)
        assert retrieved is None

    async def test_delete_todo_nonexistent(
        self, session: AsyncSession, test_user_id: int
    ):
        """Test deleting non-existent todo raises exception."""
        service = TodoService(session)

        with pytest.raises(ResourceNotFoundException):
            await service.delete_todo(
                todo_id=9999,
                user_id=test_user_id,
            )

    async def test_delete_todo_user_isolation(
        self, session: AsyncSession, test_user_id: int, other_user_id: int
    ):
        """Test that users cannot delete other users' todos."""
        service = TodoService(session)

        # Create todo for test_user
        todo = await service.create_todo(
            user_id=test_user_id,
            title="Private",
        )
        await service.commit()

        # Try to delete with other_user
        with pytest.raises(ResourceNotFoundException):
            await service.delete_todo(
                todo_id=todo.id,
                user_id=other_user_id,
            )

    async def test_todo_timestamps(self, session: AsyncSession, test_user_id: int):
        """Test that timestamps are set correctly."""
        service = TodoService(session)

        todo = await service.create_todo(
            user_id=test_user_id,
            title="Test",
        )

        assert todo.created_at is not None
        assert todo.updated_at is not None
        # Both should be recent (within 1 second) - may differ by microseconds
        assert (todo.updated_at - todo.created_at).total_seconds() < 1
