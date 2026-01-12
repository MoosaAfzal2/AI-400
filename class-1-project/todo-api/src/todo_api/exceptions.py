"""Custom exceptions for the application."""

from typing import Any, Optional


class TodoAPIException(Exception):
    """Base exception for Todo API."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        """Initialize exception.

        Args:
            message: User-friendly error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional details
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AuthenticationException(TodoAPIException):
    """Authentication failed."""

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTH_001",
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, 401, details)


class AuthorizationException(TodoAPIException):
    """Authorization failed (forbidden)."""

    def __init__(
        self,
        message: str = "Access forbidden",
        error_code: str = "AUTHZ_001",
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, 403, details)


class ValidationException(TodoAPIException):
    """Validation failed."""

    def __init__(
        self,
        message: str = "Validation error",
        error_code: str = "VALIDATION_001",
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, 422, details)


class ResourceNotFoundException(TodoAPIException):
    """Resource not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND_001",
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, 404, details)


class ConflictException(TodoAPIException):
    """Resource conflict (e.g., duplicate email)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        error_code: str = "CONFLICT_001",
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, 409, details)


class InternalServerException(TodoAPIException):
    """Internal server error."""

    def __init__(
        self,
        message: str = "Internal server error",
        error_code: str = "INTERNAL_001",
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, 500, details)
