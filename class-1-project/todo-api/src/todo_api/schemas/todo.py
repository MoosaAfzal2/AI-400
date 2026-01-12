"""Todo request and response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TodoCreate(BaseModel):
    """Create todo request."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Todo title",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional todo description",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Buy groceries",
                "description": "Buy milk, eggs, and bread",
            }
        }
    )


class TodoUpdate(BaseModel):
    """Update todo request."""

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated title",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Updated description",
    )
    is_completed: Optional[bool] = Field(
        None,
        description="Whether todo is completed",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Buy groceries",
                "is_completed": True,
            }
        }
    )


class TodoResponse(BaseModel):
    """Todo response with all fields."""

    id: int = Field(..., description="Todo ID")
    user_id: int = Field(..., description="Owner user ID")
    title: str = Field(..., description="Todo title")
    description: Optional[str] = Field(None, description="Todo description")
    is_completed: bool = Field(..., description="Whether todo is completed")
    completed_at: Optional[str] = Field(
        None, description="ISO timestamp when marked as completed"
    )
    created_at: datetime = Field(..., description="ISO timestamp when created")
    updated_at: datetime = Field(..., description="ISO timestamp when last updated")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "title": "Buy groceries",
                "description": "Buy milk, eggs, and bread",
                "is_completed": False,
                "completed_at": None,
                "created_at": "2026-01-12T12:00:00",
                "updated_at": "2026-01-12T12:00:00",
            }
        }
    )


class TodoListResponse(BaseModel):
    """Paginated list of todos."""

    items: list[TodoResponse] = Field(
        ..., description="List of todos"
    )
    total: int = Field(..., description="Total number of todos")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Number of items returned")
    has_more: bool = Field(..., description="Whether there are more items")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "title": "Buy groceries",
                        "description": "Buy milk, eggs, and bread",
                        "is_completed": False,
                        "completed_at": None,
                        "created_at": "2026-01-12T12:00:00",
                        "updated_at": "2026-01-12T12:00:00",
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 20,
                "has_more": False,
            }
        }
    )
