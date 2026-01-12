"""Token models for JWT and blacklist."""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import Base

if TYPE_CHECKING:
    from .user import User


class RefreshToken(Base, table=True):
    """Refresh token entity for token rotation.

    Attributes:
        id: Unique identifier
        user_id: Foreign key to User
        token_jti: JWT Token ID (claim) for uniqueness
        is_revoked: Whether token has been revoked
        owner: Relationship to User
    """

    __tablename__ = "refresh_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
        description="Token owner",
    )
    token_jti: str = Field(
        index=True,
        unique=True,
        nullable=False,
        description="JWT Token ID for revocation",
    )
    is_revoked: bool = Field(
        default=False,
        description="Whether token is revoked",
    )

    # Relationships
    owner: "User" = Relationship(
        back_populates="refresh_tokens",
        description="Token owner",
    )

    class Config:
        """SQLModel configuration."""

        from_attributes = True


class TokenBlacklist(Base, table=True):
    """Token blacklist for immediate revocation on logout.

    Attributes:
        id: Unique identifier
        token_jti: JWT Token ID (claim)
        user_id: User who owned the token
        blacklisted_at: When token was blacklisted
    """

    __tablename__ = "token_blacklist"

    id: Optional[int] = Field(default=None, primary_key=True)
    token_jti: str = Field(
        index=True,
        unique=True,
        nullable=False,
        description="JWT Token ID",
    )
    user_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
        description="User who owned token",
    )

    class Config:
        """SQLModel configuration."""

        from_attributes = True
