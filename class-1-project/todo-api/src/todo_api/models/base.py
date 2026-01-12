"""Base SQLModel with common fields."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Base(SQLModel):
    """Base model with timestamp fields."""

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="Timestamp when record was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="Timestamp when record was last updated",
    )

    class Config:
        """SQLModel configuration."""

        from_attributes = True
