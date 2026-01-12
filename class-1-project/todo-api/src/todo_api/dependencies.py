"""FastAPI dependency injection functions."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session
from .exceptions import AuthenticationException
from .models import User
from .security import decode_token
from sqlmodel import select


async def get_current_user(
    token: str = Depends(...),  # Will be replaced by OAuth2PasswordBearer
    session: AsyncSession = Depends(get_session),
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        session: Database session

    Returns:
        User: Current authenticated user

    Raises:
        AuthenticationException: If token is invalid or user not found
    """
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise AuthenticationException(
            message="Invalid or expired token",
            error_code="AUTH_002",
        )

    # Extract user_id from token
    user_id: Optional[int] = payload.get("sub")
    if not user_id:
        raise AuthenticationException(
            message="Invalid token claims",
            error_code="AUTH_003",
        )

    # Get user from database
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise AuthenticationException(
            message="User not found",
            error_code="AUTH_004",
        )

    if not user.is_active:
        raise AuthenticationException(
            message="User account is inactive",
            error_code="AUTH_005",
        )

    return user


async def get_optional_current_user(
    token: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None.

    Args:
        token: Optional JWT token
        session: Database session

    Returns:
        User or None
    """
    if not token:
        return None

    try:
        return await get_current_user(token, session)
    except AuthenticationException:
        return None
