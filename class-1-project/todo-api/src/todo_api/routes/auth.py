"""Authentication API routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..exceptions import (
    AuthenticationException,
    ConflictException,
    ValidationException,
)
from ..schemas import (
    ErrorResponse,
    PasswordChange,
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from ..services import AuthService, TokenService, UserService

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"},
        422: {"model": ErrorResponse, "description": "Validation failed"},
    },
)
async def register(
    data: UserRegister,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Register new user and return access token.

    Args:
        data: Registration request (email, password)
        session: Database session

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        ConflictException: If email already registered
        ValidationException: If password weak or email invalid
    """
    try:
        # Register user
        auth_service = AuthService(session)
        user = await auth_service.register_user(data.email, data.password)
        await auth_service.commit()

        # Generate tokens
        token_service = TokenService(session)
        tokens = await token_service.generate_tokens(user.id, user.email)
        await token_service.commit()

        return TokenResponse(**tokens)

    except (ConflictException, ValidationException) as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
)
async def login(
    data: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Login user and return access token.

    Args:
        data: Login request (email, password)
        session: Database session

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        AuthenticationException: If credentials invalid
    """
    try:
        # Authenticate user
        auth_service = AuthService(session)
        user = await auth_service.authenticate_user(data.email, data.password)

        # Generate tokens
        token_service = TokenService(session)
        tokens = await token_service.generate_tokens(user.id, user.email)
        await token_service.commit()

        return TokenResponse(**tokens)

    except AuthenticationException as exc:
        await session.rollback()
        raise HTTPException(status_code=401, detail=exc.message)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
    },
)
async def refresh_token(
    data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Refresh access token using refresh token.

    Args:
        data: Refresh token request
        session: Database session

    Returns:
        TokenResponse with new access token

    Raises:
        AuthenticationException: If refresh token invalid
    """
    try:
        token_service = TokenService(session)
        tokens = await token_service.refresh_access_token(data.refresh_token)
        await token_service.commit()

        return TokenResponse(**tokens)

    except AuthenticationException as exc:
        await session.rollback()
        raise HTTPException(status_code=401, detail=exc.message)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid token"},
    },
)
async def logout(
    data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Logout user by revoking refresh token.

    Args:
        data: Refresh token to revoke
        session: Database session

    Raises:
        AuthenticationException: If token invalid
    """
    try:
        token_service = TokenService(session)

        # Decode refresh token to get JTI
        from ..security import decode_token

        payload = decode_token(data.refresh_token)
        if not payload:
            raise AuthenticationException(
                message="Invalid refresh token",
                error_code="AUTH_002",
            )

        # Revoke token
        jti = payload.get("jti")
        if jti:
            await token_service.revoke_refresh_token(jti)
            await token_service.commit()

    except AuthenticationException as exc:
        await session.rollback()
        raise HTTPException(status_code=401, detail=exc.message)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        )


@router.post(
    "/change-password",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Current password incorrect"},
        422: {"model": ErrorResponse, "description": "New password invalid"},
    },
)
async def change_password(
    data: PasswordChange,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Change user password.

    Args:
        data: Current and new password
        session: Database session

    Returns:
        Updated user response

    Raises:
        AuthenticationException: If current password incorrect
        ValidationException: If new password invalid
    """
    # This endpoint requires authentication (to be added in next step)
    # For now, it's a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Requires authenticated user (coming soon)",
    )
