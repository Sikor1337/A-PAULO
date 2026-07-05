"""Defaults and rules for volunteer departure interviews."""

DEPARTURE_FIELD_TYPES = {
    "text",
    "textarea",
    "date",
    "select",
    "radio",
    "multiselect",
    "checkbox",
}
DEPARTURE_CHOICE_TYPES = {"select", "radio", "multiselect"}

DEFAULT_DEPARTURE_FIELDS = [
    {
        "key": "departure_date",
        "label": "Data odejścia",
        "field_type": "date",
        "required": True,
        "placeholder": "",
        "is_system": True,
    },
    {
        "key": "departure_reason",
        "label": "Dlaczego odchodzisz z wolontariatu?",
        "field_type": "textarea",
        "required": True,
        "placeholder": "Opisz powód odejścia",
        "is_system": True,
    },
    {
        "key": "stay_in_contact",
        "label": "Czy chcesz pozostać z nami w kontakcie?",
        "field_type": "checkbox",
        "required": False,
        "placeholder": "",
        "is_system": True,
    },
    {
        "key": "future_contact",
        "label": "W jakich sprawach możemy kontaktować się w przyszłości?",
        "field_type": "textarea",
        "required": False,
        "placeholder": "Np. jednorazowe akcje lub wydarzenia",
        "is_system": False,
    },
    {
        "key": "additional_comments",
        "label": "Dodatkowe uwagi",
        "field_type": "textarea",
        "required": False,
        "placeholder": "Co powinniśmy wiedzieć lub poprawić?",
        "is_system": False,
    },
]
