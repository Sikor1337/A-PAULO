"""Resend HTTP API backend (recommended in docs/pap-86-email-spike.md)."""

import logging

import httpx

from app.infrastructure.email.port import EmailMessage

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"
_TIMEOUT_SECONDS = 10.0


class ResendEmailBackend:
    def __init__(self, api_key: str, sender: str):
        self.api_key = api_key
        self.sender = sender

    def send(self, message: EmailMessage) -> None:
        """Send one message; failures are logged, never raised.

        Account flows must not fail because the mail provider hiccuped —
        the user can always use the resend endpoint.
        """
        try:
            response = httpx.post(
                _RESEND_ENDPOINT,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "from": self.sender,
                    "to": [message.to],
                    "subject": message.subject,
                    "html": message.html,
                },
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Resend delivery failed (to=%s)", message.to)
