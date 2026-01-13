"""Dependency injection for FastAPI routes with comprehensive authentication and role-based access control."""

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .database import get_session
from .models import User
from .security import decode_token
from .services import AuthService, TodoService

# ============================================================================
# OAuth2 Security Scheme
# ============================================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scopes={
        "access": "Access token for regular users",
        "refresh": "Refresh token to get new access token",
        "admin": "Admin scope for administrative operations",
    },
)

# ============================================================================
# Basic Type Annotations for Common Dependencies
# ============================================================================

# Session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Token dependency - raw JWT token from Authorization header
TokenDep = Annotated[str, Depends(oauth2_scheme)]


# ============================================================================
# User Extraction and Validation
# ============================================================================


async def get_current_user(
    security_scopes: SecurityScopes,
    token: TokenDep,
    session: SessionDep,
) -> User:
    """
    Extract and validate the current user from JWT token.

    Verifies:
    - Token signature and expiration
    - User exists in database
    - User is active
    - Token scopes match required scopes (if specified)

    Args:
        security_scopes: FastAPI SecurityScopes for scope validation
        token: JWT token from Authorization header
        session: Database session

    Returns:
        User object from database

    Raises:
        HTTPException: 401 Unauthorized if token invalid or user not found
    """
    # Validate token and extract claims
    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Missing user ID in token")
        user_id = int(user_id_str)

        # Check token type matches expected scope
        token_type = payload.get("type", "access")
        if security_scopes.scopes and token_type not in security_scopes.scopes:
            # Allow access token for general operations unless explicit scope required
            if token_type != "access":
                raise ValueError(f"Token type '{token_type}' not valid for this operation")

    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or missing claims",
            headers={"WWW-Authenticate": 'Bearer scope="access"'},
        ) from exc

    # Fetch user from database
    try:
        statement = select(User).where(User.id == user_id)
        result = await session.execute(statement)
        user = result.scalars().first()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": 'Bearer scope="access"'},
            )

        return user

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to validate user",
            headers={"WWW-Authenticate": 'Bearer scope="access"'},
        ) from exc


# Annotated type for current authenticated user
CurrentUserDep = Annotated[User, Security(get_current_user, scopes=["access"])]


async def get_current_admin_user(
    current_user: CurrentUserDep,
) -> User:
    """
    Verify that current user is an admin.

    Args:
        current_user: Authenticated user dependency

    Returns:
        User object if user is admin

    Raises:
        HTTPException: 403 Forbidden if user is not admin
    """
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# Annotated type for current admin user
CurrentAdminUserDep = Annotated[User, Security(get_current_admin_user, scopes=["access", "admin"])]


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    session: SessionDep = None,
) -> User | None:
    """
    Get current user if authenticated, otherwise return None.

    Useful for endpoints that work for both authenticated and unauthenticated requests.

    Args:
        token: Optional JWT token from Authorization header
        session: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not token or not session:
        return None

    try:
        security_scopes = SecurityScopes(scopes=["access"])
        return await get_current_user(security_scopes, token, session)
    except HTTPException:
        return None


# Annotated type for optional current user
CurrentUserOptionalDep = Annotated[User | None, Depends(get_current_user_optional)]


# ============================================================================
# User by URL Path Parameter
# ============================================================================


async def get_user_from_path(
    user_id: int,
    session: SessionDep,
) -> User:
    """
    Get user by ID from URL path parameter.

    Useful for admin endpoints that retrieve specific users.

    Args:
        user_id: User ID from URL path
        session: Database session

    Returns:
        User object

    Raises:
        HTTPException: 404 Not Found if user doesn't exist
    """
    try:
        statement = select(User).where(User.id == user_id)
        result = await session.execute(statement)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user",
        ) from exc


# Annotated type for user from path
UserFromPathDep = Annotated[User, Depends(get_user_from_path)]


# ============================================================================
# Service Dependencies with Injection
# ============================================================================


def get_auth_service(session: SessionDep) -> AuthService:
    """Create AuthService instance with injected session."""
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_todo_service(session: SessionDep) -> TodoService:
    """Create TodoService instance with injected session."""
    return TodoService(session)


TodoServiceDep = Annotated[TodoService, Depends(get_todo_service)]


# ============================================================================
# Composite Dependencies for Common Patterns
# ============================================================================


class AuthenticatedContext:
    """
    Composite dependency providing authenticated user and services.

    Usage:
        async def my_route(ctx: AuthenticatedContextDep) -> Response:
            user = ctx.user
            todos = await ctx.todo_service.list_todos(user.id)
    """

    def __init__(
        self,
        user: CurrentUserDep,
        session: SessionDep,
        auth_service: AuthServiceDep = None,
        todo_service: TodoServiceDep = None,
    ):
        self.user = user
        self.session = session
        self.auth_service = auth_service or AuthService(session)
        self.todo_service = todo_service or TodoService(session)

    async def commit(self) -> None:
        """Commit current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback current transaction."""
        await self.session.rollback()


def get_authenticated_context(
    user: CurrentUserDep,
    session: SessionDep,
    auth_service: AuthServiceDep,
    todo_service: TodoServiceDep,
) -> AuthenticatedContext:
    """Create AuthenticatedContext with all dependencies."""
    return AuthenticatedContext(
        user=user,
        session=session,
        auth_service=auth_service,
        todo_service=todo_service,
    )


AuthenticatedContextDep = Annotated[AuthenticatedContext, Depends(get_authenticated_context)]


# ============================================================================
# Admin Context
# ============================================================================


class AdminContext:
    """Composite dependency for admin operations."""

    def __init__(
        self,
        admin_user: CurrentAdminUserDep,
        session: SessionDep,
    ):
        self.admin_user = admin_user
        self.session = session

    async def get_user(self, user_id: int) -> User:
        """Get user by ID (admin can access any user)."""
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user


def get_admin_context(
    admin_user: CurrentAdminUserDep,
    session: SessionDep,
) -> AdminContext:
    """Create AdminContext for admin operations."""
    return AdminContext(admin_user=admin_user, session=session)


AdminContextDep = Annotated[AdminContext, Depends(get_admin_context)]
