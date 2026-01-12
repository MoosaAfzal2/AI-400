"""Pagination schemas for list responses."""

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of items to return",
    )

    class Config:
        """Schema configuration."""

        json_schema_extra = {
            "example": {
                "skip": 0,
                "limit": 10,
            }
        }


class PaginationResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Limit applied")

    class Config:
        """Schema configuration."""

        json_schema_extra = {
            "example": {
                "items": [],
                "total": 0,
                "skip": 0,
                "limit": 10,
            }
        }
