"""
Security event logging for audit trail.
Logs all security-critical events to a separate security.log file.
"""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Create security logger
security_logger = logging.getLogger("security_audit")
security_logger.setLevel(logging.INFO)
security_logger.propagate = False  # Don't propagate to root logger

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# File handler for security events
security_handler = logging.FileHandler(log_dir / "security.log")
security_handler.setLevel(logging.INFO)

# Format: timestamp | event_type | severity | details
security_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)


class SecurityEvent:
    """Security event types."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    REGISTER_SUCCESS = "register_success"
    REGISTER_FAILURE = "register_failure"
    TOKEN_INVALID = "token_invalid"
    TOKEN_EXPIRED = "token_expired"

    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # File upload events
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILURE = "file_upload_failure"
    FILE_UPLOAD_INVALID = "file_upload_invalid"
    INVALID_FILENAME = "invalid_filename"

    # Authorization events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    FORBIDDEN_ACCESS = "forbidden_access"

    # Configuration events
    WEAK_PASSWORD_ATTEMPT = "weak_password_attempt"
    INVALID_INPUT = "invalid_input"


def log_security_event(
    event_type: str,
    username: Optional[str] = None,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: str = "INFO"
):
    """
    Log a security event.

    Args:
        event_type: Type of security event (use SecurityEvent constants)
        username: Username involved in the event
        user_id: User ID involved in the event
        ip_address: IP address of the requester
        details: Additional details about the event
        severity: Severity level (INFO, WARNING, ERROR)
    """
    event_data = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "username": username,
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details or {}
    }

    log_message = json.dumps(event_data)

    # Log based on severity
    if severity == "ERROR":
        security_logger.error(log_message)
    elif severity == "WARNING":
        security_logger.warning(log_message)
    else:
        security_logger.info(log_message)
