from datetime import date, datetime
from enum import StrEnum

from app.core.audit import audit_value, calculate_delta


class _Colour(StrEnum):
    RED = "red"
    BLUE = "blue"


def test_calculate_delta_includes_changed_added_and_removed_fields() -> None:
    old_state = {"name": "Anna", "phone": "123", "obsolete": True}
    new_state = {"name": "Anna", "phone": "456", "email": "a@example.com"}

    assert calculate_delta(old_state, new_state) == {
        "phone": {"old": "123", "new": "456"},
        "obsolete": {"old": True, "new": None},
        "email": {"old": None, "new": "a@example.com"},
    }


def test_calculate_delta_returns_empty_mapping_for_identical_state() -> None:
    state = {"name": "Anna", "active": True}

    assert calculate_delta(state, dict(state)) == {}


def test_calculate_delta_detects_nullable_key_removal() -> None:
    assert calculate_delta({"optional": None}, {}) == {
        "optional": {"old": None, "new": None}
    }


def test_calculate_delta_serializes_domain_dates() -> None:
    assert calculate_delta({}, {"joined": date(2026, 7, 5)}) == {
        "joined": {"old": None, "new": "2026-07-05"}
    }


def test_audit_value_coerces_enums_and_datetimes() -> None:
    assert audit_value(_Colour.RED) == "red"
    assert audit_value(datetime(2026, 7, 5, 9, 30)) == "2026-07-05T09:30:00"


def test_audit_value_sorts_sets_and_recurses_into_containers() -> None:
    # Sets are order-unstable, so they must serialize to a deterministic order.
    assert audit_value({"b", "a", "c"}) == ["a", "b", "c"]
    assert audit_value({"tags": ({"x", "y"},), "when": date(2026, 1, 2)}) == {
        "tags": [["x", "y"]],
        "when": "2026-01-02",
    }


def test_calculate_delta_reports_enum_and_list_changes() -> None:
    delta = calculate_delta(
        {"status": _Colour.RED, "tags": ["a"]},
        {"status": _Colour.BLUE, "tags": ["a", "b"]},
    )
    assert delta == {
        "status": {"old": "red", "new": "blue"},
        "tags": {"old": ["a"], "new": ["a", "b"]},
    }
