"""Middleware for error handling and logging."""

import json
import logging
from datetime import datetime
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling and logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            # Let FastAPI exception handlers take care of it
            raise


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Extract user context if available
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id

        # Log request
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "user_id": user_id,
        }
        logger.info(f"request_start: {json.dumps(log_data)}")

        response = await call_next(request)

        # Log response
        log_data["status_code"] = response.status_code
        logger.info(f"request_end: {json.dumps(log_data)}")

        return response
