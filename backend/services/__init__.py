"""Services package for email and other external integrations."""
from .email_service import get_email_service, EmailService

__all__ = ['get_email_service', 'EmailService']
