"""Authentication request and response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        description="Password (8+ chars, uppercase, lowercase, digit, special)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }
    )


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }
    )


class TokenResponse(BaseModel):
    """Token response with access and refresh tokens."""

    access_token: str = Field(..., description="Access token (JWT)")
    refresh_token: Optional[str] = Field(
        default=None,
        description="Refresh token (JWT, only on login)",
    )
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str = Field(..., description="Refresh token from login response")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }
    )


class PasswordChange(BaseModel):
    """Password change request."""

    old_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (8+ chars, uppercase, lowercase, digit, special)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "old_password": "OldPass123!",
                "new_password": "NewPass456!",
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(
        default=None,
        description="Additional error details",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_code": "AUTH_001",
                "message": "Invalid email or password",
                "details": None,
                "timestamp": "2026-01-12T10:30:00.000Z",
            }
        }
    )


class UserResponse(BaseModel):
    """User response (for API responses, never password!)."""

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "is_active": True,
                "created_at": "2026-01-12T10:00:00.000Z",
                "updated_at": "2026-01-12T10:00:00.000Z",
            }
        }
    )
