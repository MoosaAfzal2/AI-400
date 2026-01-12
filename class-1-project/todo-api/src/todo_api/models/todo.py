"""Todo model."""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Todo(Base, table=True):
    """Todo item entity.

    Attributes:
        id: Unique todo identifier
        user_id: Foreign key to User
        title: Todo title
        description: Detailed description
        is_completed: Whether todo is completed
        completed_at: Timestamp when marked as completed
        owner: Relationship to User
    """

    __tablename__ = "todos"

    id: Optional[int] = Field(default=None, primary_key=True, description="Todo ID")
    user_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
        description="Owner user ID",
    )
    title: str = Field(
        nullable=False,
        min_length=1,
        max_length=255,
        description="Todo title",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Detailed description",
    )
    is_completed: bool = Field(
        default=False,
        nullable=False,
        description="Whether todo is completed",
    )
    completed_at: Optional[str] = Field(
        default=None,
        description="Timestamp when marked as completed",
    )

    # Relationships
    owner: "User" = Relationship(
        back_populates="todos",
    )

    class Config:
        """SQLModel configuration."""

        from_attributes = True
