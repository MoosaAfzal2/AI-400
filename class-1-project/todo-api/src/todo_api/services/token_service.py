"""Token service for JWT and token blacklist management."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import uuid

from ..config import settings
from ..exceptions import AuthenticationException, ResourceNotFoundException
from ..models import RefreshToken, TokenBlacklist
from ..security import create_access_token, create_refresh_token, decode_token


class TokenService:
    """Service for token management (JWT, refresh tokens, blacklist)."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: AsyncSession for database operations
        """
        self.session = session

    def _generate_jti(self) -> str:
        """Generate unique JWT ID (jti claim).

        Returns:
            Unique UUID string
        """
        return str(uuid.uuid4())

    async def generate_tokens(self, user_id: int, email: str) -> dict:
        """Generate access and refresh tokens for user.

        Args:
            user_id: User ID
            email: User email

        Returns:
            Dict with access_token, refresh_token, token_type, expires_in
        """
        # Generate unique JTI for both tokens
        access_jti = self._generate_jti()
        refresh_jti = self._generate_jti()

        # Create token claims
        access_claims = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "jti": access_jti,
        }
        refresh_claims = {
            "sub": user_id,
            "email": email,
            "type": "refresh",
            "jti": refresh_jti,
        }

        # Create tokens
        access_token = create_access_token(access_claims)
        refresh_token = create_refresh_token(refresh_claims)

        # Store refresh token in database
        db_refresh_token = RefreshToken(
            user_id=user_id,
            token_jti=refresh_jti,
            is_revoked=False,
        )
        self.session.add(db_refresh_token)
        await self.session.flush()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def validate_token(self, token: str) -> dict:
        """Validate JWT token (signature, expiration, blacklist).

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            AuthenticationException: If token invalid
        """
        # Decode token
        payload = decode_token(token)
        if not payload:
            raise AuthenticationException(
                message="Invalid or expired token",
                error_code="AUTH_002",
            )

        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti:
            is_blacklisted = await self._is_token_blacklisted(jti)
            if is_blacklisted:
                raise AuthenticationException(
                    message="Token has been revoked",
                    error_code="AUTH_006",
                )

        return payload

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Generate new access token using refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            Dict with new access_token, token_type, expires_in

        Raises:
            AuthenticationException: If refresh token invalid
        """
        # Validate refresh token
        payload = await self.validate_token(refresh_token)

        # Check token type
        if payload.get("type") != "refresh":
            raise AuthenticationException(
                message="Invalid token type",
                error_code="AUTH_007",
            )

        # Get refresh token record
        refresh_jti = payload.get("jti")
        db_token = await self.get_refresh_token_by_jti(refresh_jti)

        if not db_token or db_token.is_revoked:
            raise AuthenticationException(
                message="Refresh token is invalid or revoked",
                error_code="AUTH_006",
            )

        # Generate new access token
        user_id = payload.get("sub")
        email = payload.get("email")

        access_jti = self._generate_jti()
        access_claims = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "jti": access_jti,
        }
        access_token = create_access_token(access_claims)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def revoke_refresh_token(self, jti: str) -> None:
        """Revoke refresh token by JTI (logout).

        Args:
            jti: Token JTI
        """
        # Mark refresh token as revoked
        statement = select(RefreshToken).where(RefreshToken.token_jti == jti)
        result = await self.session.execute(statement)
        token = result.scalars().first()

        if token:
            token.is_revoked = True
            self.session.add(token)
            await self.session.flush()

        # Add to blacklist
        blacklisted = TokenBlacklist(
            token_jti=jti,
            user_id=token.user_id if token else 0,
        )
        self.session.add(blacklisted)
        await self.session.flush()

    async def blacklist_token(self, user_id: int, jti: str) -> None:
        """Add token to blacklist (for logout).

        Args:
            user_id: User ID
            jti: Token JTI
        """
        blacklisted = TokenBlacklist(
            token_jti=jti,
            user_id=user_id,
        )
        self.session.add(blacklisted)
        await self.session.flush()

    async def get_refresh_token_by_jti(self, jti: str) -> Optional[RefreshToken]:
        """Get refresh token record by JTI.

        Args:
            jti: Token JTI

        Returns:
            RefreshToken or None
        """
        statement = select(RefreshToken).where(RefreshToken.token_jti == jti)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is in blacklist.

        Args:
            jti: Token JTI

        Returns:
            True if blacklisted, False otherwise
        """
        statement = select(TokenBlacklist).where(TokenBlacklist.token_jti == jti)
        result = await self.session.execute(statement)
        return result.scalars().first() is not None

    async def commit(self) -> None:
        """Commit transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        await self.session.rollback()
