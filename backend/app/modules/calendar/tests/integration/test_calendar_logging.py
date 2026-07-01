import logging

from app.modules.calendar.services.logging import CalendarFeedAccessLogFilter


def test_access_log_filter_redacts_private_feed_token() -> None:
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='%s - "%s %s HTTP/%s" %d',
        args=(
            "127.0.0.1",
            "GET",
            "/api/v1/calendar-feeds/top-secret-token.ics",
            "1.1",
            200,
        ),
        exc_info=None,
    )

    CalendarFeedAccessLogFilter().filter(record)

    assert "top-secret-token" not in str(record.args)
    assert "/api/v1/calendar-feeds/[redacted].ics" in str(record.args)
