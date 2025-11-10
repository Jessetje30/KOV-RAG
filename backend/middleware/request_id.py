"""
Request ID middleware for tracking requests across the application.
"""
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add a unique request ID to each request.

    The request ID is:
    - Generated as a UUID for each request
    - Added to request.state for use in route handlers
    - Added to response headers as X-Request-ID
    - Logged with each request for tracing
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add request ID.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with X-Request-ID header
        """
        # Check if client provided a request ID
        request_id = request.headers.get("X-Request-ID")

        # Generate new ID if not provided
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in request state for access in route handlers
        request.state.request_id = request_id

        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )

        # Process request
        try:
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}",
                extra={"request_id": request_id, "status_code": response.status_code}
            )

            return response

        except Exception as e:
            # Log request error
            logger.error(
                f"Request failed: {request.method} {request.url.path} - Error: {str(e)}",
                extra={"request_id": request_id},
                exc_info=True
            )
            raise


def get_request_id(request: Request) -> str:
    """
    Helper function to get request ID from request state.

    Args:
        request: Current request

    Returns:
        Request ID string
    """
    return getattr(request.state, "request_id", "unknown")
