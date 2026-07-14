"""Tests for shared configurable-field rules."""

from app.modules.recruitment.services.form_fields import allocate_field_key


def test_allocate_field_key_normalizes_polish_text_and_avoids_collisions() -> None:
    used_keys = {"zrodlo_zgloszenia", "zrodlo_zgloszenia_2"}

    key = allocate_field_key("Źródło zgłoszenia", used_keys)

    assert key == "zrodlo_zgloszenia_3"
    assert key in used_keys


def test_allocate_field_key_uses_fallback_for_non_ascii_label() -> None:
    assert allocate_field_key("你好", set()) == "pytanie"
