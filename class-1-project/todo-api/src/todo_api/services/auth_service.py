"""Authentication service for user registration and login."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import AuthenticationException, ValidationException
from ..models import User
from ..security import hash_password, verify_password, validate_password
from .user_service import UserService


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: AsyncSession for database operations
        """
        self.user_service = UserService(session)

    async def register_user(self, email: str, password: str) -> User:
        """Register new user with email and password.

        Args:
            email: User email address
            password: Plain text password

        Returns:
            Created User

        Raises:
            ValidationException: If password is weak
            ConflictException: If email already exists
        """
        # Validate email format (basic check)
        if not email or "@" not in email:
            raise ValidationException(
                message="Invalid email format",
                error_code="VALIDATION_001",
            )

        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            raise ValidationException(
                message=error_msg,
                error_code="VALIDATION_002",
                details={"field": "password"},
            )

        # Create user
        user = await self.user_service.create_user(email, password)
        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise

        Raises:
            AuthenticationException: If credentials invalid
        """
        # Get user by email
        user = await self.user_service.get_user_by_email(email)
        if not user:
            raise AuthenticationException(
                message="Invalid email or password",
                error_code="AUTH_001",
            )

        # Check if active
        if not user.is_active:
            raise AuthenticationException(
                message="User account is inactive",
                error_code="AUTH_005",
            )

        # Verify password
        if not verify_password(password, user.password_hash):
            raise AuthenticationException(
                message="Invalid email or password",
                error_code="AUTH_001",
            )

        return user

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> User:
        """Change user password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            Updated User

        Raises:
            AuthenticationException: If old password invalid
            ValidationException: If new password weak
        """
        # Get user
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise AuthenticationException(
                message="User not found",
                error_code="AUTH_004",
            )

        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise AuthenticationException(
                message="Current password is incorrect",
                error_code="AUTH_001",
            )

        # Validate new password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            raise ValidationException(
                message=error_msg,
                error_code="VALIDATION_002",
                details={"field": "password"},
            )

        # Update password
        user = await self.user_service.update_user(
            user_id,
            password_hash=hash_password(new_password),
        )
        return user

    async def commit(self) -> None:
        """Commit transaction."""
        await self.user_service.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        await self.user_service.rollback()
