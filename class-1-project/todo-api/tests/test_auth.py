"""Authentication tests following TDD approach."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.todo_api.exceptions import (
    AuthenticationException,
    ConflictException,
    ValidationException,
)
from src.todo_api.models import User
from src.todo_api.services import AuthService, TokenService, UserService
from src.todo_api.security import verify_password


class TestUserService:
    """Tests for UserService CRUD operations."""

    async def test_create_user(self, session: AsyncSession):
        """Test creating a new user."""
        service = UserService(session)

        user = await service.create_user("user@example.com", "TestPass123!")

        assert user.email == "user@example.com"
        assert user.is_active is True
        assert verify_password("TestPass123!", user.password_hash)

    async def test_create_duplicate_user(self, session: AsyncSession, test_user: User):
        """Test that duplicate email raises ConflictException."""
        service = UserService(session)

        with pytest.raises(ConflictException):
            await service.create_user("test@example.com", "TestPass123!")

    async def test_get_user_by_email(self, session: AsyncSession, test_user: User):
        """Test retrieving user by email."""
        service = UserService(session)

        user = await service.get_user_by_email("test@example.com")

        assert user is not None
        assert user.email == "test@example.com"

    async def test_get_user_by_email_not_found(self, session: AsyncSession):
        """Test that non-existent email returns None."""
        service = UserService(session)

        user = await service.get_user_by_email("nonexistent@example.com")

        assert user is None

    async def test_get_user_by_id(self, session: AsyncSession, test_user: User):
        """Test retrieving user by ID."""
        service = UserService(session)

        user = await service.get_user_by_id(test_user.id)

        assert user is not None
        assert user.id == test_user.id

    async def test_get_user_by_id_not_found(self, session: AsyncSession):
        """Test that non-existent ID returns None."""
        service = UserService(session)

        user = await service.get_user_by_id(999)

        assert user is None

    async def test_delete_user(self, session: AsyncSession, test_user: User):
        """Test soft-deleting a user."""
        service = UserService(session)

        await service.delete_user(test_user.id)
        await service.commit()

        user = await service.get_user_by_id(test_user.id)
        assert user.is_active is False


class TestAuthService:
    """Tests for AuthService authentication."""

    async def test_register_user(self, session: AsyncSession):
        """Test user registration."""
        service = AuthService(session)

        user = await service.register_user("newuser@example.com", "SecurePass123!")

        assert user.email == "newuser@example.com"
        assert verify_password("SecurePass123!", user.password_hash)

    async def test_register_invalid_email(self, session: AsyncSession):
        """Test registration with invalid email."""
        service = AuthService(session)

        with pytest.raises(ValidationException):
            await service.register_user("invalidemail", "SecurePass123!")

    async def test_register_weak_password(self, session: AsyncSession):
        """Test registration with weak password."""
        service = AuthService(session)

        with pytest.raises(ValidationException):
            await service.register_user("user@example.com", "weak")

    async def test_register_duplicate_email(self, session: AsyncSession, test_user: User):
        """Test registration with duplicate email."""
        service = AuthService(session)

        with pytest.raises(ConflictException):
            await service.register_user("test@example.com", "SecurePass123!")

    async def test_authenticate_user(self, session: AsyncSession, test_user: User):
        """Test user authentication."""
        service = AuthService(session)

        user = await service.authenticate_user("test@example.com", "TestPass123!")

        assert user.id == test_user.id

    async def test_authenticate_invalid_email(self, session: AsyncSession):
        """Test authentication with non-existent email."""
        service = AuthService(session)

        with pytest.raises(AuthenticationException):
            await service.authenticate_user("nonexistent@example.com", "password")

    async def test_authenticate_invalid_password(
        self, session: AsyncSession, test_user: User
    ):
        """Test authentication with wrong password."""
        service = AuthService(session)

        with pytest.raises(AuthenticationException):
            await service.authenticate_user("test@example.com", "WrongPassword123!")

    async def test_authenticate_inactive_user(
        self, session: AsyncSession, test_user: User
    ):
        """Test authentication with inactive user."""
        service = UserService(session)
        await service.update_user(test_user.id, is_active=False)
        await service.commit()

        auth_service = AuthService(session)
        with pytest.raises(AuthenticationException):
            await auth_service.authenticate_user("test@example.com", "TestPass123!")


class TestTokenService:
    """Tests for TokenService JWT management."""

    async def test_generate_tokens(self, session: AsyncSession, test_user: User):
        """Test generating access and refresh tokens."""
        service = TokenService(session)

        tokens = await service.generate_tokens(test_user.id, test_user.email)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] > 0

    async def test_validate_token(self, session: AsyncSession, test_user: User):
        """Test token validation."""
        service = TokenService(session)

        tokens = await service.generate_tokens(test_user.id, test_user.email)
        payload = await service.validate_token(tokens["access_token"])

        assert payload["sub"] == test_user.id
        assert payload["email"] == test_user.email
        assert payload["type"] == "access"

    async def test_validate_invalid_token(self, session: AsyncSession):
        """Test validating invalid token."""
        service = TokenService(session)

        with pytest.raises(AuthenticationException):
            await service.validate_token("invalid.token.here")

    async def test_refresh_access_token(self, session: AsyncSession, test_user: User):
        """Test refreshing access token."""
        service = TokenService(session)

        tokens = await service.generate_tokens(test_user.id, test_user.email)
        new_tokens = await service.refresh_access_token(tokens["refresh_token"])

        assert "access_token" in new_tokens
        assert new_tokens["token_type"] == "bearer"
        assert new_tokens["expires_in"] > 0

    async def test_revoke_token(self, session: AsyncSession, test_user: User):
        """Test revoking refresh token."""
        service = TokenService(session)

        tokens = await service.generate_tokens(test_user.id, test_user.email)
        payload = await service.validate_token(tokens["refresh_token"])
        jti = payload["jti"]

        await service.revoke_refresh_token(jti)
        await service.commit()

        with pytest.raises(AuthenticationException):
            await service.validate_token(tokens["refresh_token"])

    async def test_blacklist_token(self, session: AsyncSession, test_user: User):
        """Test blacklisting a token."""
        service = TokenService(session)

        tokens = await service.generate_tokens(test_user.id, test_user.email)
        payload = await service.validate_token(tokens["access_token"])
        jti = payload["jti"]

        await service.blacklist_token(test_user.id, jti)
        await service.commit()

        with pytest.raises(AuthenticationException):
            await service.validate_token(tokens["access_token"])
