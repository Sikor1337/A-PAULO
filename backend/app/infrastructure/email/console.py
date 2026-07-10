"""Development/test backend: logs messages instead of sending them."""

import logging

from app.infrastructure.email.port import EmailMessage

logger = logging.getLogger(__name__)


class ConsoleEmailBackend:
    def send(self, message: EmailMessage) -> None:
        logger.info(
            "E-mail (console backend) to=%s subject=%r\n%s",
            message.to,
            message.subject,
            message.html,
        )
        # Printed (not just logged) so the link is always visible in the dev
        # console regardless of the app's logging level — this backend exists
        # precisely to surface that link.
        print(
            "\n===== E-MAIL (console backend) =====\n"
            f"To:      {message.to}\n"
            f"Subject: {message.subject}\n"
            f"{message.html}\n"
            "====================================\n",
            flush=True,
        )
