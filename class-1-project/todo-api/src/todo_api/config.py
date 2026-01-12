"""Application configuration using Pydantic Settings."""

from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/todoapi"

    # JWT Configuration
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str = "your-super-secret-key-minimum-32-characters-long"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Bcrypt Configuration
    BCRYPT_COST_FACTOR: int = 10

    # Server Configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = True

    # CORS Configuration
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
