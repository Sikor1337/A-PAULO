"""Beneficiary recruitment defaults and public-link constants (PAP-90)."""

BENEFICIARY_RECRUITMENT_ROUTE_PREFIX = "/beneficiary-application"
BENEFICIARY_RECRUITMENT_TOKEN_HEADER = "X-Beneficiary-Recruitment-Token"

BENEFICIARY_RECRUITMENT_STATUSES = {
    "NEW",
    "BENEFICIARY_CREATED",
    "REJECTED",
    "ARCHIVED",
}

BENEFICIARY_DEFAULT_FIELDS = [
    {
        "key": "full_name",
        "label": "Imię i nazwisko osoby potrzebującej pomocy",
        "field_type": "text",
        "required": True,
        "placeholder": "np. Jan Kowalski",
        "is_system": True,
    },
    {
        "key": "address",
        "label": "Adres zamieszkania",
        "field_type": "text",
        "required": True,
        "placeholder": "Ulica, numer, miejscowość",
        "is_system": True,
    },
    {
        "key": "phone",
        "label": "Telefon osoby potrzebującej pomocy",
        "field_type": "tel",
        "required": False,
        "placeholder": "+48 123 456 789",
        "is_system": True,
    },
    {
        "key": "reporter_name",
        "label": "Imię i nazwisko osoby zgłaszającej",
        "field_type": "text",
        "required": True,
        "placeholder": "Osoba do kontaktu",
        "is_system": True,
    },
    {
        "key": "reporter_phone",
        "label": "Telefon osoby zgłaszającej",
        "field_type": "tel",
        "required": True,
        "placeholder": "+48 123 456 789",
        "is_system": True,
    },
    {
        "key": "help_needed",
        "label": "Opis sytuacji i oczekiwanej pomocy",
        "field_type": "textarea",
        "required": True,
        "placeholder": "Opisz sytuację i najważniejsze potrzeby",
        "is_system": True,
    },
    {
        "key": "rodo_consent",
        "label": (
            "Wyrażam zgodę na przetwarzanie podanych danych "
            "w celu organizacji pomocy"
        ),
        "field_type": "checkbox",
        "required": True,
        "placeholder": "",
        "is_system": True,
    },
]
