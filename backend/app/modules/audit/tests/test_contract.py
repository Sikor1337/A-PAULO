from datetime import date

from app.core.audit import calculate_delta


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
