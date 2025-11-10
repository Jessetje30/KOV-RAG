"""Security utilities for frontend."""
import html
import re
from typing import Any


def sanitize_html(text: str) -> str:
    """
    Sanitize text to prevent XSS attacks.
    Escapes all HTML special characters.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for HTML rendering
    """
    if not text:
        return ""
    return html.escape(str(text))


def sanitize_for_display(value: Any) -> str:
    """
    Sanitize any value for safe display in UI.

    Args:
        value: Value to sanitize (will be converted to string)

    Returns:
        Sanitized string safe for display
    """
    return sanitize_html(str(value))


def is_safe_url(url: str) -> bool:
    """
    Check if a URL is safe (prevents javascript: and data: URLs).

    Args:
        url: URL to check

    Returns:
        True if URL is safe, False otherwise
    """
    if not url:
        return False

    url_lower = url.lower().strip()

    # Block dangerous protocols
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:']
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return False

    # Only allow http, https, and relative URLs
    if url_lower.startswith(('http://', 'https://', '/', '#')):
        return True

    # Relative URLs without protocol are OK
    if not ':' in url_lower.split('/')[0]:
        return True

    return False


def validate_input(text: str, min_length: int = 0, max_length: int = 1000,
                   allow_special_chars: bool = True) -> tuple[bool, str]:
    """
    Validate user input text.

    Args:
        text: Text to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        allow_special_chars: Whether to allow special characters

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Invoer mag niet leeg zijn"

    text = text.strip()

    if len(text) < min_length:
        return False, f"Invoer moet minimaal {min_length} tekens bevatten"

    if len(text) > max_length:
        return False, f"Invoer mag maximaal {max_length} tekens bevatten"

    # Check for suspicious patterns that might indicate XSS attempts
    dangerous_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]

    if not allow_special_chars:
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Ongeldige invoer gedetecteerd"

    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not email.strip():
        return False, "Email mag niet leeg zijn"

    email = email.strip()

    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False, "Ongeldig email formaat"

    if len(email) > 254:  # RFC 5321
        return False, "Email adres is te lang"

    return True, ""


def validate_query(query: str) -> tuple[bool, str]:
    """
    Validate query input for RAG system.

    Args:
        query: Query text to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_input(
        query,
        min_length=3,
        max_length=2000,
        allow_special_chars=True
    )
