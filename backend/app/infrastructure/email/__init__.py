"""Outbound e-mail infrastructure (PAP-87)."""

from app.infrastructure.email.console import ConsoleEmailBackend
from app.infrastructure.email.port import EmailMessage, EmailPort
from app.infrastructure.email.resend import ResendEmailBackend

__all__ = ["ConsoleEmailBackend", "EmailMessage", "EmailPort", "ResendEmailBackend"]
