"""Shared constants for the recruitment domain."""

DEFAULT_FIELDS = [
    {
        "key": "full_name",
        "label": "Imię i nazwisko",
        "field_type": "text",
        "required": True,
        "placeholder": "np. Jan Kowalski",
        "is_system": True,
    },
    {
        "key": "email",
        "label": "Adres e-mail",
        "field_type": "email",
        "required": True,
        "placeholder": "email@example.com",
        "is_system": True,
    },
    {
        "key": "phone",
        "label": "Telefon",
        "field_type": "tel",
        "required": True,
        "placeholder": "+48 123 456 789",
        "is_system": True,
    },
    {
        "key": "social_link",
        "label": "Link do profilu społecznościowego",
        "field_type": "text",
        "required": False,
        "placeholder": "https://...",
        "is_system": False,
    },
    {
        "key": "availability",
        "label": "Dyspozycyjność",
        "field_type": "textarea",
        "required": False,
        "placeholder": "Napisz, w jakie dni i godziny jesteś dostępny/a",
        "is_system": False,
    },
]

ALLOWED_FIELD_TYPES = {
    "text",
    "textarea",
    "email",
    "tel",
    "date",
    "select",
    "radio",
    "multiselect",
    "checkbox",
}
SINGLE_CHOICE_FIELD_TYPES = {"select", "radio"}
MULTIPLE_CHOICE_FIELD_TYPES = {"multiselect"}
CHOICE_FIELD_TYPES = SINGLE_CHOICE_FIELD_TYPES | MULTIPLE_CHOICE_FIELD_TYPES

SUBMISSION_STATUSES = {
    "SUBMITTED",
    "ONBOARDING",
    "ACCEPTED",
    "REJECTED",
    "RETURNED",
}

NEW_VOLUNTEER_STATUS = "new_volunteer"
REGULAR_USER_STATUS = "regular"
MIGRATED_RECRUITMENT_PASSWORD = "!migration-unusable!"
STAFF_STATUSES = {"regular", "admin"}

RECRUITMENT_ROUTE_PREFIX = "/recrutation"
RECRUITMENT_TOKEN_HEADER = "X-Recruitment-Token"

ANSWER_MAX_LENGTHS = {
    "full_name": 200,
    "email": 255,
    "phone": 30,
    "social_link": 500,
    "availability": 10_000,
}
MAX_ANSWERS_JSON_SIZE = 100_000
MAX_SHORT_ANSWER_LENGTH = 2_000
MAX_LONG_ANSWER_LENGTH = 10_000
