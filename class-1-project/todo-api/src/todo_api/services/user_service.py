"""User service for CRUD operations."""

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..exceptions import ConflictException, ResourceNotFoundException
from ..models import User
from ..security import hash_password


class UserService:
    """Service for user-related database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: AsyncSession for database operations
        """
        self.session = session

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address.

        Args:
            email: User email

        Returns:
            User or None if not found
        """
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User or None if not found
        """
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def create_user(self, email: str, password: str) -> User:
        """Create new user with hashed password.

        Args:
            email: User email (must be unique)
            password: Plain text password (will be hashed)

        Returns:
            Created User

        Raises:
            ConflictException: If email already exists
        """
        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = User(email=email, password_hash=password_hash, is_active=True)

        try:
            self.session.add(user)
            await self.session.flush()  # Get the ID without committing
            return user
        except IntegrityError as exc:
            await self.session.rollback()
            if "unique constraint" in str(exc).lower() or "email" in str(exc).lower():
                raise ConflictException(
                    message="Email already registered",
                    error_code="CONFLICT_001",
                    details={"email": email},
                )
            raise

    async def update_user(
        self,
        user_id: int,
        **kwargs,
    ) -> User:
        """Update user fields.

        Args:
            user_id: User ID
            **kwargs: Fields to update

        Returns:
            Updated User

        Raises:
            ResourceNotFoundException: If user not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundException(
                message="User not found",
                error_code="NOT_FOUND_001",
            )

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        self.session.add(user)
        await self.session.flush()
        return user

    async def delete_user(self, user_id: int) -> None:
        """Delete user by ID (soft delete via is_active).

        Args:
            user_id: User ID

        Raises:
            ResourceNotFoundException: If user not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundException(
                message="User not found",
                error_code="NOT_FOUND_001",
            )

        # Soft delete
        user.is_active = False
        self.session.add(user)
        await self.session.flush()

    async def commit(self) -> None:
        """Commit transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        await self.session.rollback()
