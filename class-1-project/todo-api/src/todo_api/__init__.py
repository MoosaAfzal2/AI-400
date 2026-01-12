"""Todo API application factory and entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import close_db, init_db


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

    # TODO: Add routes here
    # from .routes import auth_router, todo_router
    # app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
    # app.include_router(todo_router, prefix="/api/v1/todos", tags=["todos"])

    # TODO: Add health check endpoint
    # @app.get("/health", tags=["health"])
    # async def health_check():
    #     return {"status": "healthy"}

    return app


def main() -> None:
    """Entry point for CLI."""
    import uvicorn

    app = create_app()
    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
