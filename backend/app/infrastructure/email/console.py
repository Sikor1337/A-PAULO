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
