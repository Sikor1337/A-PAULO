"""Prevent private calendar subscription tokens from reaching access logs."""

import logging
import re

TOKEN_PATH = re.compile(r"/api/v1/calendar-feeds/[^/?\s]+\.ics")


class CalendarFeedAccessLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(
                TOKEN_PATH.sub("/api/v1/calendar-feeds/[redacted].ics", value)
                if isinstance(value, str)
                else value
                for value in record.args
            )
        if isinstance(record.msg, str):
            record.msg = TOKEN_PATH.sub(
                "/api/v1/calendar-feeds/[redacted].ics", record.msg
            )
        return True


def install_calendar_access_log_filter() -> None:
    logger = logging.getLogger("uvicorn.access")
    if not any(
        isinstance(item, CalendarFeedAccessLogFilter) for item in logger.filters
    ):
        logger.addFilter(CalendarFeedAccessLogFilter())
