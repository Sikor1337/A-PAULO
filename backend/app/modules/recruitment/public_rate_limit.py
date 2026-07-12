"""Small in-process safety net for the public beneficiary form.

The deployment should additionally enforce edge limits in a reverse proxy/CDN.
"""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status

_lock = Lock()
_per_ip: dict[str, deque[float]] = defaultdict(deque)
_global: deque[float] = deque()


def _trim(entries: deque[float], cutoff: float) -> None:
    while entries and entries[0] <= cutoff:
        entries.popleft()


def rate_limit_public_beneficiary_form(request: Request) -> None:
    """Allow 30 requests/minute per source and 300/minute per worker."""
    now = monotonic()
    ip = request.client.host if request.client else "unknown"
    with _lock:
        if len(_per_ip) > 10_000:
            stale_ips = [
                address
                for address, entries in _per_ip.items()
                if not entries or entries[-1] <= now - 60
            ]
            for address in stale_ips:
                _per_ip.pop(address, None)
        own = _per_ip[ip]
        _trim(own, now - 60)
        _trim(_global, now - 60)
        if len(own) >= 30 or len(_global) >= 300:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Zbyt wiele prób. Spróbuj ponownie za minutę.",
                headers={"Retry-After": "60"},
            )
        own.append(now)
        _global.append(now)
