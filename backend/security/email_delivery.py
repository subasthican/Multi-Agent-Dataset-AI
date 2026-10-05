"""Password-reset delivery. No token is returned through a public API."""
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


def send_reset_email(email: str, token: str) -> bool:
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM")
    if not host or not sender:
        logger.warning("Password reset delivery unavailable: SMTP is not configured.")
        return False
    base = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = email
    message["Subject"] = "Reset your DATA NEBULA AI password"
    message.set_content(f"Use this single-use link within 30 minutes:\n{base}/reset-password?{urlencode({'token': token})}\n\nIgnore this email if you did not request a reset.")
    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=10) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if os.getenv("SMTP_USERNAME"):
                smtp.login(os.environ["SMTP_USERNAME"], os.environ.get("SMTP_PASSWORD", ""))
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError):
        # Do not log message contents, token, SMTP password or email address.
        logger.warning("Password reset delivery failed.")
        return False
    return True
