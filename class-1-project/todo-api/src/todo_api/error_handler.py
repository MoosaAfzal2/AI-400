"""Error handling middleware and utilities."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized error response format."""

    error_code: str = "INTERNAL_001"
    message: str
    details: Optional[Any] = None
    timestamp: str
    request_id: Optional[str] = None

    class Config:
        """Schema configuration."""

        json_schema_extra = {
            "example": {
                "error_code": "VALIDATION_001",
                "message": "Email is required",
                "details": {"field": "email"},
                "timestamp": "2026-01-12T20:30:00Z",
                "request_id": "req-abc123",
            }
        }


def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Any] = None,
    request_id: Optional[str] = None,
) -> ErrorResponse:
    """Create standardized error response.

    Args:
        error_code: Machine-readable error code
        message: User-friendly error message
        details: Additional error details
        request_id: Request ID for tracking

    Returns:
        ErrorResponse instance
    """
    return ErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
        timestamp=datetime.utcnow().isoformat() + "Z",
        request_id=request_id,
    )


# Error code to HTTP status mapping
ERROR_CODE_MAP = {
    # Authentication (401)
    "AUTH_001": 401,
    "AUTH_002": 401,
    "AUTH_003": 401,
    "AUTH_004": 401,
    "AUTH_005": 401,
    "AUTH_006": 401,
    "AUTH_007": 401,
    # Authorization (403)
    "AUTHZ_001": 403,
    "AUTHZ_002": 403,
    # Validation (422)
    "VALIDATION_001": 422,
    "VALIDATION_002": 422,
    "VALIDATION_003": 422,
    "VALIDATION_004": 422,
    "VALIDATION_005": 422,
    "VALIDATION_006": 422,
    "VALIDATION_007": 422,
    "VALIDATION_008": 422,
    # Resource (404)
    "NOT_FOUND_001": 404,
    "NOT_FOUND_002": 404,
    # Conflict (409)
    "CONFLICT_001": 409,
    # Server (500)
    "INTERNAL_001": 500,
    "SERVER_001": 500,
    "SERVER_002": 500,
    "SERVER_003": 500,
    "SERVER_004": 500,
}


def get_http_status_for_error_code(error_code: str) -> int:
    """Get HTTP status code for error code.

    Args:
        error_code: Error code string

    Returns:
        HTTP status code (defaults to 500)
    """
    return ERROR_CODE_MAP.get(error_code, 500)
