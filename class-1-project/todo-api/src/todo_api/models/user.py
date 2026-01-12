"""User model."""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import Base

if TYPE_CHECKING:
    from .todo import Todo
    from .token import RefreshToken


class User(Base, table=True):
    """User entity with authentication fields.

    Attributes:
        id: Unique user identifier
        email: User email (unique)
        password_hash: Hashed password (never stored in plain text)
        is_active: Whether user account is active
        todos: Relationship to user's todo items
        refresh_tokens: Relationship to user's refresh tokens
    """

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True, description="User ID")
    email: str = Field(
        index=True,
        unique=True,
        nullable=False,
        description="User email address",
    )
    password_hash: str = Field(
        nullable=False,
        description="Hashed password (bcrypt)",
    )
    is_active: bool = Field(
        default=True,
        nullable=False,
        description="Whether user is active",
    )

    # Relationships
    todos: list["Todo"] = Relationship(
        back_populates="owner",
        cascade_delete=True,
    )
    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="owner",
        cascade_delete=True,
    )

    class Config:
        """SQLModel configuration."""

        from_attributes = True
