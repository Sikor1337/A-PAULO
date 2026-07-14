"""Seed the reference data required by a new A-PAULO environment.

Run this once after Alembic during every deployment::

    python -m scripts.seed_required_data

The operation is transactional and idempotent. It creates missing bootstrap
records and repairs protected invariants without overwriting configuration
that administrators are allowed to customize.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.departments.models import Department
from app.modules.pi.models import Function, Group, SystemFunctionKey
from app.modules.recruitment.models import (
    BeneficiaryRecruitmentField,
    DepartureField,
    RecruitmentField,
)
from app.modules.security.models import Permission, UserGroup
from app.modules.security.models import constants as permission_constants

PERMISSIONS = (
    ("CAN_VIEW_USERS", "Podgląd użytkowników", "Użytkownicy", False),
    ("CAN_MANAGE_USERS", "Zarządzanie użytkownikami", "Użytkownicy", False),
    ("CAN_VIEW_VOLUNTEERS", "Podgląd wolontariuszy", "Wolontariusze", True),
    (
        "CAN_MANAGE_VOLUNTEERS",
        "Zarządzanie wolontariuszami",
        "Wolontariusze",
        True,
    ),
    ("CAN_VIEW_BENEFICIARIES", "Podgląd podopiecznych", "Podopieczni", True),
    (
        "CAN_MANAGE_BENEFICIARIES",
        "Zarządzanie podopiecznymi",
        "Podopieczni",
        True,
    ),
    ("CAN_VIEW_PI_GROUPS", "Podgląd grup A-PAULO", "Grupy A-PAULO", True),
    (
        "CAN_MANAGE_PI_GROUPS",
        "Zarządzanie grupami A-PAULO",
        "Grupy A-PAULO",
        True,
    ),
    ("CAN_VIEW_FUNCTIONS", "Podgląd funkcji", "Funkcje", True),
    ("CAN_MANAGE_FUNCTIONS", "Zarządzanie funkcjami", "Funkcje", True),
    (
        "CAN_VIEW_ATTACHMENTS",
        "Podgląd załączników i kart BO",
        "Załączniki",
        True,
    ),
    (
        "CAN_MANAGE_ATTACHMENTS",
        "Zarządzanie załącznikami i kartami BO",
        "Załączniki",
        True,
    ),
    ("CAN_VIEW_RECRUITMENT", "Podgląd rekrutacji", "Rekrutacja", True),
    (
        "CAN_MANAGE_RECRUITMENT",
        "Zarządzanie rekrutacją",
        "Rekrutacja",
        True,
    ),
    ("CAN_VIEW_EVENTS", "Podgląd wydarzeń", "Wydarzenia", True),
    ("CAN_MANAGE_EVENTS", "Zarządzanie wydarzeniami", "Wydarzenia", True),
    ("CAN_VIEW_SECURITY", "Podgląd grup użytkowników", "Bezpieczeństwo", False),
    (
        "CAN_MANAGE_SECURITY",
        "Zarządzanie grupami i uprawnieniami",
        "Bezpieczeństwo",
        False,
    ),
    ("CAN_VIEW_DEPARTMENTS", "Podgląd działów", "Działy", True),
    ("CAN_MANAGE_DEPARTMENTS", "Zarządzanie działami", "Działy", True),
    (
        "CAN_VIEW_BUG_REPORTS",
        "Podgląd zgłoszeń błędów",
        "Zgłoszenia błędów",
        True,
    ),
    (
        "CAN_MANAGE_BUG_REPORTS",
        "Rozwiązywanie zgłoszeń błędów",
        "Zgłoszenia błędów",
        True,
    ),
    (
        "CAN_SUBMIT_BUG_REPORTS",
        "Zgłaszanie błędów",
        "Zgłoszenia błędów",
        True,
    ),
    ("CAN_VIEW_TASKS", "Podgląd zadań", "Zadania", True),
    ("CAN_MANAGE_TASKS", "Zarządzanie zadaniami", "Zadania", True),
    (
        "CAN_SUBMIT_DEPARTURE_SURVEY",
        "Wypełnianie ankiety odejścia",
        "Ankieta odejścia",
        True,
    ),
)

SECURITY_GROUPS = (
    {
        "system_key": "admin",
        "name": "Admin",
        "description": "Pełny dostęp administracyjny",
    },
    {
        "system_key": "staff",
        "name": "Staff",
        "description": "Domyślne uprawnienia pracownika",
    },
)

SYSTEM_FUNCTIONS = (
    {
        "system_key": SystemFunctionKey.GROUP_GUIDE.value,
        "name": "Przewodnik",
    },
    {
        "system_key": SystemFunctionKey.BENEFICIARY_LEADER.value,
        "name": "Lider Podopiecznego",
    },
)

PI_GROUPS = tuple(
    {"system_key": f"GROUP_{letter}", "name": f"Grupa {letter}"} for letter in "ABCD"
)

DEPARTMENTS = (
    ("INDIVIDUAL_HELP", "Pomoc indywidualna", "🤝"),
    ("RENOVATIONS", "Remonty", "🔨"),
    ("CLEANING", "Grupa porządkowa", "🧹"),
    ("PHYSIOTHERAPY", "Fizjoterapia", "💪"),
    ("ACCOUNTING", "Księgowość", "💰"),
    ("SENIOR_FESTIVAL", "Festyn Seniora", "🎉"),
    ("TRAINING", "Szkolenia", "📚"),
    ("MEDIA", "Media", "📱"),
    ("SENIOR_CLUB", "Klub seniora", "🏠"),
    ("MUSIC", "Muzyczni", "🎵"),
    ("GASTRONOMY", "Gastronomia", "🍽️"),
    ("FUNDRAISING", "Zbieranie funduszy", "💵"),
)

VOLUNTEER_RECRUITMENT_FIELDS = (
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
)

DEPARTURE_FIELDS = (
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
)

BENEFICIARY_RECRUITMENT_FIELDS = (
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
            "Wyrażam zgodę na przetwarzanie podanych danych w celu organizacji pomocy"
        ),
        "field_type": "checkbox",
        "required": True,
        "placeholder": "",
        "is_system": True,
    },
)


@dataclass
class SeedReport:
    """Summary used by deployment logs and regression tests."""

    created: Counter[str] = field(default_factory=Counter)
    updated: Counter[str] = field(default_factory=Counter)

    def mark_created(self, category: str) -> None:
        self.created[category] += 1

    def mark_updated(self, category: str) -> None:
        self.updated[category] += 1


def _set_changed(entity: Any, values: Mapping[str, Any]) -> bool:
    changed = False
    for attribute, expected in values.items():
        if getattr(entity, attribute) != expected:
            setattr(entity, attribute, expected)
            changed = True
    return changed


def _validate_permission_catalog() -> None:
    declared_codes = {
        value
        for name, value in vars(permission_constants).items()
        if name.startswith("CAN_") and isinstance(value, str)
    }
    seeded_codes = {code for code, _, _, _ in PERMISSIONS}
    if declared_codes != seeded_codes:
        missing = sorted(declared_codes - seeded_codes)
        obsolete = sorted(seeded_codes - declared_codes)
        raise RuntimeError(
            "Permission seed and application constants differ: "
            f"missing={missing}, obsolete={obsolete}"
        )


def seed_security_reference_data(
    session: Session, report: SeedReport | None = None
) -> SeedReport:
    """Upsert the permission catalog and the two built-in security groups."""
    report = report or SeedReport()
    _validate_permission_catalog()

    existing_permissions = {
        permission.code: permission for permission in session.query(Permission).all()
    }
    created_permission_codes: set[str] = set()
    for code, name, category, _ in PERMISSIONS:
        permission = existing_permissions.get(code)
        if permission is None:
            permission = Permission(code=code, name=name, category=category)
            session.add(permission)
            existing_permissions[code] = permission
            created_permission_codes.add(code)
            report.mark_created("permissions")
        elif _set_changed(permission, {"name": name, "category": category}):
            report.mark_updated("permissions")

    session.flush()
    all_permissions = list(existing_permissions.values())
    default_staff_codes = {
        code for code, _, _, granted_to_staff in PERMISSIONS if granted_to_staff
    }

    for definition in SECURITY_GROUPS:
        system_key = definition["system_key"]
        group = session.query(UserGroup).filter_by(system_key=system_key).one_or_none()
        created = group is None
        if group is None:
            same_name = (
                session.query(UserGroup).filter_by(name=definition["name"]).first()
            )
            if same_name is not None:
                raise RuntimeError(
                    f"Cannot create system group {system_key!r}: "
                    f"name {definition['name']!r} is already used"
                )
            group = UserGroup(
                **definition,
                is_system=True,
            )
            session.add(group)
            report.mark_created("security_groups")
        else:
            changed = _set_changed(
                group,
                {
                    "name": definition["name"],
                    "description": definition["description"],
                    "is_system": True,
                },
            )
            if changed:
                report.mark_updated("security_groups")

        if system_key == "admin":
            expected = all_permissions
        elif created:
            expected = [
                permission
                for permission in all_permissions
                if permission.code in default_staff_codes
            ]
        else:
            expected_by_code = {
                permission.code: permission for permission in group.permissions
            }
            expected_by_code.update(
                {
                    code: existing_permissions[code]
                    for code in created_permission_codes & default_staff_codes
                }
            )
            expected = list(expected_by_code.values())

        if {item.code for item in group.permissions} != {
            item.code for item in expected
        }:
            group.permissions = expected
            if not created:
                report.mark_updated("security_groups")

    return report


def seed_system_functions(
    session: Session, report: SeedReport | None = None
) -> SeedReport:
    """Create stable SQL records for functions derived by business rules."""
    report = report or SeedReport()
    for definition in SYSTEM_FUNCTIONS:
        function = (
            session.query(Function)
            .filter_by(system_key=definition["system_key"])
            .one_or_none()
        )
        if function is None:
            function = (
                session.query(Function)
                .filter_by(name=definition["name"], system_key=None)
                .one_or_none()
            )
        if function is None:
            session.add(
                Function(
                    **definition,
                    is_system=True,
                    is_active=True,
                )
            )
            report.mark_created("functions")
            continue
        if _set_changed(
            function,
            {"system_key": definition["system_key"], "is_system": True},
        ):
            report.mark_updated("functions")
    return report


def seed_pi_groups(session: Session, report: SeedReport | None = None) -> SeedReport:
    """Create the basic beneficiary groups A-D without overwriting later renames."""
    report = report or SeedReport()
    for definition in PI_GROUPS:
        group = (
            session.query(Group)
            .filter_by(system_key=definition["system_key"])
            .one_or_none()
        )
        if group is None:
            group = (
                session.query(Group)
                .filter_by(name=definition["name"], system_key=None)
                .one_or_none()
            )
        if group is None:
            session.add(Group(**definition))
            report.mark_created("pi_groups")
        elif group.system_key is None:
            group.system_key = definition["system_key"]
            report.mark_updated("pi_groups")
    return report


def seed_departments(session: Session, report: SeedReport | None = None) -> SeedReport:
    """Create the twelve initial departments without undoing user configuration."""
    report = report or SeedReport()
    for system_key, name, icon in DEPARTMENTS:
        department = (
            session.query(Department).filter_by(system_key=system_key).one_or_none()
        )
        if department is None:
            department = (
                session.query(Department)
                .filter_by(name=name, system_key=None)
                .one_or_none()
            )
        if department is None:
            session.add(
                Department(
                    system_key=system_key,
                    name=name,
                    icon=icon,
                    description="",
                    is_archived=False,
                )
            )
            report.mark_created("departments")
        elif department.system_key is None:
            department.system_key = system_key
            report.mark_updated("departments")
    return report


def _seed_form_fields(
    session: Session,
    model: type[Any],
    definitions: Sequence[Mapping[str, Any]],
    category: str,
    report: SeedReport,
) -> None:
    current = session.query(model).order_by(model.position, model.id).all()
    table_was_empty = not current
    by_key = {item.key: item for item in current}

    for position, definition in enumerate(definitions):
        if not table_was_empty and not definition["is_system"]:
            continue
        key = str(definition["key"])
        item = by_key.get(key)
        if item is None:
            item = model(
                **definition,
                options=[],
                position=position,
                is_active=True,
            )
            session.add(item)
            by_key[key] = item
            current.append(item)
            report.mark_created(category)
            continue

        if definition["is_system"] and _set_changed(
            item,
            {
                "field_type": definition["field_type"],
                "required": definition["required"],
                "is_active": True,
                "is_system": True,
            },
        ):
            report.mark_updated(category)

    system_keys = [
        str(definition["key"]) for definition in definitions if definition["is_system"]
    ]
    ordered = [by_key[key] for key in system_keys]
    ordered.extend(item for item in current if item.key not in system_keys)
    for position, item in enumerate(ordered):
        if item.position != position:
            item.position = position
            report.mark_updated(category)


def seed_recruitment_fields(
    session: Session, report: SeedReport | None = None
) -> SeedReport:
    """Seed questions for volunteer, departure and beneficiary forms."""
    report = report or SeedReport()
    _seed_form_fields(
        session,
        RecruitmentField,
        VOLUNTEER_RECRUITMENT_FIELDS,
        "volunteer_recruitment_fields",
        report,
    )
    _seed_form_fields(
        session,
        DepartureField,
        DEPARTURE_FIELDS,
        "departure_fields",
        report,
    )
    _seed_form_fields(
        session,
        BeneficiaryRecruitmentField,
        BENEFICIARY_RECRUITMENT_FIELDS,
        "beneficiary_recruitment_fields",
        report,
    )
    return report


def load_required_data(session: Session) -> SeedReport:
    """Load every required reference-data family in one transaction boundary."""
    report = SeedReport()
    seed_security_reference_data(session, report)
    seed_system_functions(session, report)
    seed_pi_groups(session, report)
    seed_departments(session, report)
    seed_recruitment_fields(session, report)
    session.flush()
    return report


def _format_counts(values: Counter[str]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(values.items())) or "0"


def main() -> None:
    settings = get_settings()
    schema = settings.database_schema or "public"
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise SystemExit("Invalid DATABASE_SCHEMA")

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    if engine.dialect.name == "postgresql":
        schema_sql = engine.dialect.identifier_preparer.quote(schema)

        @event.listens_for(engine, "begin")
        def set_search_path(connection) -> None:
            connection.exec_driver_sql(f"SET LOCAL search_path TO {schema_sql}")

    try:
        with Session(engine) as session:
            try:
                report = load_required_data(session)
                session.commit()
            except Exception:
                session.rollback()
                raise
    finally:
        engine.dispose()

    print(f"{schema}: required data seed complete")
    print(f"created: {_format_counts(report.created)}")
    print(f"updated: {_format_counts(report.updated)}")


if __name__ == "__main__":
    main()
