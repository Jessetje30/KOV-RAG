"""Security middleware for adding security headers and HTTPS enforcement."""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Enforce HTTPS
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """

    def __init__(self, app, enforce_https: bool = False):
        super().__init__(app)
        self.enforce_https = enforce_https

    async def dispatch(self, request: Request, call_next):
        """Process request and add security headers to response."""

        # HTTPS enforcement (redirect HTTP to HTTPS)
        if self.enforce_https:
            if request.url.scheme == "http" and request.headers.get("X-Forwarded-Proto") != "https":
                # Build HTTPS URL
                https_url = request.url.replace(scheme="https")
                return RedirectResponse(url=str(https_url), status_code=301)

        # Process request
        response: Response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS header (only add if HTTPS is used)
        if request.url.scheme == "https" or request.headers.get("X-Forwarded-Proto") == "https":
            # max-age=31536000 (1 year), includeSubDomains, preload
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Content Security Policy
        # Allows connections to same origin and to backend API
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # For Streamlit frontend
            "style-src 'self' 'unsafe-inline'",  # For inline styles
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' http://localhost:* https://localhost:*",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy)
        permissions_directives = [
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_directives)

        return response
