"""E-mail sending port: services depend on this, not on a concrete provider."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    html: str


class EmailPort(Protocol):
    def send(self, message: EmailMessage) -> None:
        """Deliver one message; implementations must not raise on failure."""
        ...
