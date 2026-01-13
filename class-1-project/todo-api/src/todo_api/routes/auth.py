"""Authentication API routes."""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..dependencies import (
    AuthServiceDep,
    CurrentUserDep,
    SessionDep,
)
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
from ..security import decode_token, verify_password
from ..services import TokenService

logger = logging.getLogger(__name__)
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
    auth_service: AuthServiceDep,
    session: SessionDep,
) -> TokenResponse:
    """Register new user and return access token.

    Args:
        data: Registration request (email, password)
        auth_service: Injected auth service
        session: Database session

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        ConflictException: If email already registered
        ValidationException: If password weak or email invalid
    """
    try:
        # Register user
        user = await auth_service.register_user(data.email, data.password)
        await session.commit()

        # Generate tokens
        token_service = TokenService(session)
        tokens = await token_service.generate_tokens(user.id, user.email)
        await session.commit()

        return TokenResponse(**tokens)

    except (ConflictException, ValidationException) as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        await session.rollback()
        logger.exception("Register failed with exception: %s", str(exc))
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
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep,
    session: SessionDep,
) -> TokenResponse:
    """Login user and return access token.

    OAuth2 compatible token login endpoint. The username field from OAuth2PasswordRequestForm
    is mapped to email for authentication.

    Args:
        form_data: OAuth2 password request form (username, password)
        auth_service: Injected auth service
        session: Database session

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        AuthenticationException: If credentials invalid
    """
    try:
        # Authenticate user using form_data.username as email (OAuth2 standard)
        user = await auth_service.authenticate_user(form_data.username, form_data.password)

        # Generate tokens
        token_service = TokenService(session)
        tokens = await token_service.generate_tokens(user.id, user.email)
        await session.commit()

        return TokenResponse(**tokens)

    except AuthenticationException as exc:
        await session.rollback()
        raise HTTPException(status_code=401, detail=exc.message)
    except Exception as exc:
        await session.rollback()
        logger.exception("Login failed with exception: %s", str(exc))
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
    session: SessionDep,
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
        await session.commit()

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
    session: SessionDep,
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
            await session.commit()

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
    current_user: CurrentUserDep,
    data: PasswordChange,
    auth_service: AuthServiceDep,
    session: SessionDep,
) -> UserResponse:
    """Change user password.

    Args:
        current_user: Currently authenticated user
        data: Current and new password
        auth_service: Injected auth service
        session: Database session

    Returns:
        Updated user response

    Raises:
        AuthenticationException: If current password incorrect
        ValidationException: If new password invalid
    """
    try:
        # Change password (includes old password verification inside)
        await auth_service.change_password(
            current_user.id,
            data.current_password,
            data.new_password,
        )
        await session.commit()

        return UserResponse.model_validate(current_user, from_attributes=True)

    except (AuthenticationException, ValidationException) as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )
