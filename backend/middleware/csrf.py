"""
CSRF protection middleware for FastAPI.

Note: Since we use JWT Bearer tokens (not session cookies for auth),
CSRF is less of a concern. This middleware is optional and can be
enabled for specific endpoints if needed.
"""
import secrets
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Optional CSRF protection middleware.

    Since this API uses JWT Bearer tokens (Authorization header),
    it's already protected against CSRF attacks. This middleware
    is provided for completeness but may not be necessary.

    Traditional CSRF attacks rely on browsers automatically sending
    cookies. JWT Bearer tokens are explicitly added by JavaScript
    and won't be sent automatically by the browser.
    """

    def __init__(self, app, exempt_paths: Optional[list] = None):
        """
        Initialize CSRF protection.

        Args:
            app: FastAPI application
            exempt_paths: List of paths to exempt from CSRF checks
        """
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/api/health",
            "/api/auth/login",
            "/api/auth/register",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]

    async def dispatch(self, request: Request, call_next):
        """
        Check CSRF token for state-changing operations.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip CSRF check for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # Only check state-changing methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)

        # For Bearer token auth, CSRF is not applicable
        # The token is explicitly added by JavaScript, not automatically by browser
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Token-based auth is inherently CSRF-safe
            return await call_next(request)

        # If using cookie-based auth (which we don't), check CSRF token
        # This is here for completeness but won't be triggered in our app
        csrf_token_header = request.headers.get("X-CSRF-Token")
        csrf_token_cookie = request.cookies.get("csrf_token")

        if not csrf_token_header or not csrf_token_cookie:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing"
            )

        if csrf_token_header != csrf_token_cookie:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token invalid"
            )

        return await call_next(request)


def generate_csrf_token() -> str:
    """
    Generate a secure CSRF token.

    Returns:
        Random secure token string
    """
    return secrets.token_urlsafe(32)
