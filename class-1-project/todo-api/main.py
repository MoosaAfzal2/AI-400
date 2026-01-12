"""Entry point for the Todo API application."""

import uvicorn

from src.todo_api import create_app


def main() -> None:
    """Run the Todo API server.

    Usage:
        python -m src.todo_api.main

    Environment Variables:
        SERVER_HOST: Server host (default: 0.0.0.0)
        SERVER_PORT: Server port (default: 8000)
        DEBUG: Enable debug mode (default: false)
    """
    app = create_app()

    from src.todo_api.config import settings

    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    main()
