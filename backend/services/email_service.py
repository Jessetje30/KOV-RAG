"""
Modern email service for sending invitations.
Supports both Resend API (recommended) and SMTP as fallback.
"""
import os
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

logger = logging.getLogger(__name__)


class EmailService:
    """Email service supporting Resend API and SMTP."""

    def __init__(self):
        """Initialize email service with configuration from environment."""
        self.email_provider = os.getenv("EMAIL_PROVIDER", "smtp")  # 'resend' or 'smtp'
        self.from_email = os.getenv("EMAIL_FROM", "noreply@example.com")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "BBL RAG")
        self.app_url = os.getenv("FRONTEND_URL", "http://localhost:8501")

        if self.email_provider == "resend":
            self.resend_api_key = os.getenv("RESEND_API_KEY")
            if not self.resend_api_key:
                logger.warning("RESEND_API_KEY not set, falling back to SMTP")
                self.email_provider = "smtp"

        if self.email_provider == "smtp":
            self.smtp_host = os.getenv("SMTP_HOST", "localhost")
            self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
            self.smtp_username = os.getenv("SMTP_USERNAME")
            self.smtp_password = os.getenv("SMTP_PASSWORD")
            self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    def send_invitation_email(self, to_email: str, invitation_token: str, invited_by_name: str) -> bool:
        """
        Send invitation email to a new user.

        Args:
            to_email: Recipient email address
            invitation_token: Secure invitation token
            invited_by_name: Name of the admin who sent the invitation

        Returns:
            bool: True if email sent successfully
        """
        setup_url = f"{self.app_url}/setup-account?token={invitation_token}"

        subject = f"Uitnodiging voor BBL RAG - Kijk op Veiligheid"

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px; margin: 20px 0;">
        <h1 style="color: #2c3e50; margin-bottom: 20px;">🏗️ BBL RAG - Kijk op Veiligheid</h1>

        <p style="font-size: 16px; color: #555;">Hallo,</p>

        <p style="font-size: 16px; color: #555;">
            Je bent uitgenodigd door <strong>{invited_by_name}</strong> om toegang te krijgen tot de BBL RAG applicatie.
        </p>

        <p style="font-size: 16px; color: #555;">
            Met deze applicatie kun je het Besluit Bouwwerken Leefomgeving (BBL) doorzoeken met AI-ondersteuning.
        </p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{setup_url}"
               style="display: inline-block; padding: 15px 30px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                Account Aanmaken
            </a>
        </div>

        <p style="font-size: 14px; color: #777;">
            Of kopieer deze link naar je browser:<br>
            <a href="{setup_url}" style="color: #3498db; word-break: break-all;">{setup_url}</a>
        </p>

        <p style="font-size: 14px; color: #777; margin-top: 30px;">
            Deze uitnodiging is 7 dagen geldig.
        </p>

        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

        <p style="font-size: 12px; color: #999; text-align: center;">
            BBL RAG - Besluit Bouwwerken Leefomgeving<br>
            Dit is een automatisch gegenereerde email. Gelieve niet te antwoorden.
        </p>
    </div>
</body>
</html>
"""

        text_body = f"""
BBL RAG - Kijk op Veiligheid

Hallo,

Je bent uitgenodigd door {invited_by_name} om toegang te krijgen tot de BBL RAG applicatie.

Met deze applicatie kun je het Besluit Bouwwerken Leefomgeving (BBL) doorzoeken met AI-ondersteuning.

Klik op de volgende link om je account aan te maken:
{setup_url}

Deze uitnodiging is 7 dagen geldig.

---
BBL RAG - Besluit Bouwwerken Leefomgeving
Dit is een automatisch gegenereerde email. Gelieve niet te antwoorden.
"""

        try:
            if self.email_provider == "resend":
                return self._send_via_resend(to_email, subject, html_body, text_body)
            else:
                return self._send_via_smtp(to_email, subject, html_body, text_body)
        except Exception as e:
            logger.error(f"Failed to send invitation email to {to_email}: {str(e)}")
            return False

    def _send_via_resend(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email via Resend API."""
        try:
            import resend
            resend.api_key = self.resend_api_key

            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_body,
                "text": text_body
            }

            email = resend.Emails.send(params)
            logger.info(f"Email sent successfully via Resend to {to_email} (ID: {email['id']})")
            return True

        except Exception as e:
            logger.error(f"Resend API error: {str(e)}")
            return False

    def _send_via_smtp(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email via SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')

            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully via SMTP to {to_email}")
            return True

        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
