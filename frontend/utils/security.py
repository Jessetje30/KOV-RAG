"""Security utilities for frontend - OOP refactored."""
import html
import re
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    error_message: str = ""

    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.is_valid


class Sanitizer:
    """HTML and URL sanitization utilities."""

    DANGEROUS_PROTOCOLS = ['javascript:', 'data:', 'vbscript:']
    SAFE_PROTOCOLS = ['http://', 'https://', '/', '#']

    @staticmethod
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

    @staticmethod
    def sanitize_for_display(value: Any) -> str:
        """
        Sanitize any value for safe display in UI.

        Args:
            value: Value to sanitize (will be converted to string)

        Returns:
            Sanitized string safe for display
        """
        return Sanitizer.sanitize_html(str(value))

    @staticmethod
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
        for protocol in Sanitizer.DANGEROUS_PROTOCOLS:
            if url_lower.startswith(protocol):
                return False

        # Allow safe protocols
        if url_lower.startswith(Sanitizer.SAFE_PROTOCOLS):
            return True

        # Relative URLs without protocol are OK
        if ':' not in url_lower.split('/')[0]:
            return True

        return False


class InputValidator:
    """Input validation utilities with XSS detection."""

    # Dangerous patterns that might indicate XSS attempts
    XSS_PATTERNS = [
        r'<script[^>]*>',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]

    # Email validation pattern (RFC 5321 compliant)
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    MAX_EMAIL_LENGTH = 254

    @staticmethod
    def validate_text(
        text: str,
        min_length: int = 0,
        max_length: int = 1000,
        check_xss: bool = True,
        field_name: str = "Invoer"
    ) -> ValidationResult:
        """
        Validate user input text.

        Args:
            text: Text to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            check_xss: Whether to check for XSS patterns
            field_name: Name of field for error messages

        Returns:
            ValidationResult object
        """
        if not text or not text.strip():
            return ValidationResult(False, f"{field_name} mag niet leeg zijn")

        text = text.strip()

        if len(text) < min_length:
            return ValidationResult(
                False,
                f"{field_name} moet minimaal {min_length} tekens bevatten"
            )

        if len(text) > max_length:
            return ValidationResult(
                False,
                f"{field_name} mag maximaal {max_length} tekens bevatten"
            )

        # Check for suspicious XSS patterns
        if check_xss:
            for pattern in InputValidator.XSS_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    return ValidationResult(False, "Ongeldige invoer gedetecteerd")

        return ValidationResult(True)

    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """
        Validate email format (RFC 5321 compliant).

        Args:
            email: Email address to validate

        Returns:
            ValidationResult object
        """
        if not email or not email.strip():
            return ValidationResult(False, "Email mag niet leeg zijn")

        email = email.strip()

        # Check length (RFC 5321)
        if len(email) > InputValidator.MAX_EMAIL_LENGTH:
            return ValidationResult(False, "Email adres is te lang")

        # Check format
        if not re.match(InputValidator.EMAIL_PATTERN, email):
            return ValidationResult(False, "Ongeldig email formaat")

        return ValidationResult(True)

    @staticmethod
    def validate_query(query: str) -> ValidationResult:
        """
        Validate query input for RAG system.

        Args:
            query: Query text to validate

        Returns:
            ValidationResult object
        """
        return InputValidator.validate_text(
            query,
            min_length=3,
            max_length=2000,
            check_xss=True,
            field_name="Vraag"
        )

    @staticmethod
    def validate_password(
        password: str,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True
    ) -> ValidationResult:
        """
        Validate password strength.

        Args:
            password: Password to validate
            min_length: Minimum password length
            require_uppercase: Require at least one uppercase letter
            require_lowercase: Require at least one lowercase letter
            require_digit: Require at least one digit
            require_special: Require at least one special character

        Returns:
            ValidationResult object
        """
        if not password:
            return ValidationResult(False, "Wachtwoord mag niet leeg zijn")

        if len(password) < min_length:
            return ValidationResult(
                False,
                f"Wachtwoord moet minimaal {min_length} tekens bevatten"
            )

        if require_uppercase and not re.search(r'[A-Z]', password):
            return ValidationResult(
                False,
                "Wachtwoord moet minimaal één hoofdletter bevatten"
            )

        if require_lowercase and not re.search(r'[a-z]', password):
            return ValidationResult(
                False,
                "Wachtwoord moet minimaal één kleine letter bevatten"
            )

        if require_digit and not re.search(r'\d', password):
            return ValidationResult(
                False,
                "Wachtwoord moet minimaal één cijfer bevatten"
            )

        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return ValidationResult(
                False,
                "Wachtwoord moet minimaal één speciaal teken bevatten"
            )

        return ValidationResult(True)


# Backward compatibility - legacy function interface
def sanitize_html(text: str) -> str:
    """Legacy function - use Sanitizer.sanitize_html() instead."""
    return Sanitizer.sanitize_html(text)


def validate_email(email: str) -> tuple[bool, str]:
    """Legacy function - use InputValidator.validate_email() instead."""
    result = InputValidator.validate_email(email)
    return result.is_valid, result.error_message


def validate_query(query: str) -> tuple[bool, str]:
    """Legacy function - use InputValidator.validate_query() instead."""
    result = InputValidator.validate_query(query)
    return result.is_valid, result.error_message
