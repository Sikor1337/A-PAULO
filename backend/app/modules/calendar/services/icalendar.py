"""Small RFC 5545 serializer used by calendar feeds and event downloads."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.modules.calendar.models import CalendarEvent
from app.modules.calendar.models.constants import CANCELLED_STATUS


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _timestamp(value: datetime) -> str:
    return _utc(value).strftime("%Y%m%dT%H%M%SZ")


def _fold(line: str) -> list[str]:
    if len(line.encode("utf-8")) <= 75:
        return [line]
    rows: list[str] = []
    current = ""
    for character in line:
        candidate = current + character
        limit = 74 if rows else 75
        if len(candidate.encode("utf-8")) > limit:
            rows.append(current)
            current = " " + character
        else:
            current = candidate
    rows.append(current)
    return rows


def _event_lines(event: CalendarEvent) -> list[str]:
    lines = [
        "BEGIN:VEVENT",
        f"UID:{_escape(event.uid)}",
        f"DTSTAMP:{_timestamp(event.updated_at)}",
        f"SEQUENCE:{event.sequence}",
    ]
    if event.is_all_day:
        timezone = ZoneInfo(event.timezone)
        start_date = _utc(event.starts_at).astimezone(timezone).date()
        end_date = _utc(event.ends_at).astimezone(timezone).date()
        if end_date <= start_date:
            end_date = start_date + timedelta(days=1)
        lines.extend(
            [
                f"DTSTART;VALUE=DATE:{start_date:%Y%m%d}",
                f"DTEND;VALUE=DATE:{end_date:%Y%m%d}",
            ]
        )
    else:
        lines.extend(
            [
                f"DTSTART:{_timestamp(event.starts_at)}",
                f"DTEND:{_timestamp(event.ends_at)}",
            ]
        )
    lines.append(f"SUMMARY:{_escape(event.title)}")
    if event.location:
        lines.append(f"LOCATION:{_escape(event.location)}")
    if event.recurrence_rule:
        lines.append(f"RRULE:{event.recurrence_rule}")
    lines.append(
        "STATUS:CANCELLED" if event.status == CANCELLED_STATUS else "STATUS:CONFIRMED"
    )
    lines.append("END:VEVENT")
    return lines


def serialize_calendar(events: list[CalendarEvent], name: str = "A-PAULO") -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "PRODID:-//A-PAULO//Wydarzenia//PL",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(name)}",
    ]
    for event in events:
        lines.extend(_event_lines(event))
    lines.append("END:VCALENDAR")
    folded = [row for line in lines for row in _fold(line)]
    return "\r\n".join(folded) + "\r\n"
