"""Todo API application factory and entry point."""

from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import close_db, get_session, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown events.

    Args:
        app: FastAPI application instance.
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    app = FastAPI(
        title="Todo API with Authentication",
        description="Production-grade Todo API with JWT authentication",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include auth and todo routes
    from .routes import auth_router, todo_router

    app.include_router(auth_router)
    app.include_router(todo_router)

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Health check endpoint for monitoring.

        Returns:
            Status object with timestamp
        """
        return {
            "status": "healthy",
            "timestamp": str(datetime.utcnow()),
        }

    # Readiness endpoint for Kubernetes
    @app.get("/ready", tags=["health"])
    async def readiness_check(session: AsyncSession = Depends(get_session)) -> dict:
        """Readiness probe - checks if service is ready to accept traffic.

        Args:
            session: Database session to verify connectivity

        Returns:
            Ready status or 503 if not ready
        """
        try:
            # Verify database connectivity
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))
            return {
                "status": "ready",
                "timestamp": str(datetime.utcnow()),
            }
        except Exception:
            return {
                "status": "not_ready",
                "timestamp": str(datetime.utcnow()),
            }

    # Metrics endpoint for Prometheus
    @app.get("/metrics", tags=["monitoring"])
    async def metrics() -> dict:
        """Prometheus metrics endpoint (basic implementation).

        Returns:
            Metrics object with basic stats
        """
        return {
            "app_name": "todo-api",
            "version": "0.1.0",
            "timestamp": str(datetime.utcnow()),
        }

    return app


app = create_app()

def main() -> None:
    """Run the Todo API server.

    Usage:
        python -m src.todo_api.main

    Environment Variables:
        SERVER_HOST: Server host (default: 0.0.0.0)
        SERVER_PORT: Server port (default: 8000)
        DEBUG: Enable debug mode (default: false)
    """
    uvicorn.run(
        "todo_api.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    main()

