"""Stable permission codes and built-in user-group definitions."""

CAN_VIEW_USERS = "CAN_VIEW_USERS"
CAN_MANAGE_USERS = "CAN_MANAGE_USERS"
CAN_VIEW_VOLUNTEERS = "CAN_VIEW_VOLUNTEERS"
CAN_MANAGE_VOLUNTEERS = "CAN_MANAGE_VOLUNTEERS"
CAN_VIEW_BENEFICIARIES = "CAN_VIEW_BENEFICIARIES"
CAN_MANAGE_BENEFICIARIES = "CAN_MANAGE_BENEFICIARIES"
CAN_VIEW_PI_GROUPS = "CAN_VIEW_PI_GROUPS"
CAN_MANAGE_PI_GROUPS = "CAN_MANAGE_PI_GROUPS"
CAN_VIEW_FUNCTIONS = "CAN_VIEW_FUNCTIONS"
CAN_MANAGE_FUNCTIONS = "CAN_MANAGE_FUNCTIONS"
CAN_VIEW_ATTACHMENTS = "CAN_VIEW_ATTACHMENTS"
CAN_MANAGE_ATTACHMENTS = "CAN_MANAGE_ATTACHMENTS"
CAN_VIEW_RECRUITMENT = "CAN_VIEW_RECRUITMENT"
CAN_MANAGE_RECRUITMENT = "CAN_MANAGE_RECRUITMENT"
CAN_VIEW_EVENTS = "CAN_VIEW_EVENTS"
CAN_MANAGE_EVENTS = "CAN_MANAGE_EVENTS"
CAN_VIEW_SECURITY = "CAN_VIEW_SECURITY"
CAN_MANAGE_SECURITY = "CAN_MANAGE_SECURITY"
CAN_VIEW_DEPARTMENTS = "CAN_VIEW_DEPARTMENTS"
CAN_MANAGE_DEPARTMENTS = "CAN_MANAGE_DEPARTMENTS"
CAN_VIEW_BUG_REPORTS = "CAN_VIEW_BUG_REPORTS"
CAN_MANAGE_BUG_REPORTS = "CAN_MANAGE_BUG_REPORTS"

PERMISSION_CATALOG = (
    (CAN_VIEW_USERS, "Podgląd użytkowników", "Użytkownicy"),
    (CAN_MANAGE_USERS, "Zarządzanie użytkownikami", "Użytkownicy"),
    (CAN_VIEW_VOLUNTEERS, "Podgląd wolontariuszy", "Wolontariusze"),
    (CAN_MANAGE_VOLUNTEERS, "Zarządzanie wolontariuszami", "Wolontariusze"),
    (CAN_VIEW_BENEFICIARIES, "Podgląd podopiecznych", "Podopieczni"),
    (CAN_MANAGE_BENEFICIARIES, "Zarządzanie podopiecznymi", "Podopieczni"),
    (CAN_VIEW_PI_GROUPS, "Podgląd grup A-PAULO", "Grupy A-PAULO"),
    (CAN_MANAGE_PI_GROUPS, "Zarządzanie grupami A-PAULO", "Grupy A-PAULO"),
    (CAN_VIEW_FUNCTIONS, "Podgląd funkcji", "Funkcje"),
    (CAN_MANAGE_FUNCTIONS, "Zarządzanie funkcjami", "Funkcje"),
    (CAN_VIEW_ATTACHMENTS, "Podgląd załączników i kart BO", "Załączniki"),
    (CAN_MANAGE_ATTACHMENTS, "Zarządzanie załącznikami i kartami BO", "Załączniki"),
    (CAN_VIEW_RECRUITMENT, "Podgląd rekrutacji", "Rekrutacja"),
    (CAN_MANAGE_RECRUITMENT, "Zarządzanie rekrutacją", "Rekrutacja"),
    (CAN_VIEW_EVENTS, "Podgląd wydarzeń", "Wydarzenia"),
    (CAN_MANAGE_EVENTS, "Zarządzanie wydarzeniami", "Wydarzenia"),
    (CAN_VIEW_SECURITY, "Podgląd grup użytkowników", "Bezpieczeństwo"),
    (CAN_MANAGE_SECURITY, "Zarządzanie grupami i uprawnieniami", "Bezpieczeństwo"),
    (CAN_VIEW_DEPARTMENTS, "Podgląd działów", "Działy"),
    (CAN_MANAGE_DEPARTMENTS, "Zarządzanie działami", "Działy"),
    (CAN_VIEW_BUG_REPORTS, "Podgląd zgłoszeń błędów", "Zgłoszenia błędów"),
    (CAN_MANAGE_BUG_REPORTS, "Rozwiązywanie zgłoszeń błędów", "Zgłoszenia błędów"),
)

ALL_PERMISSION_CODES = frozenset(code for code, _, _ in PERMISSION_CATALOG)
STAFF_PERMISSION_CODES = frozenset(
    code
    for code in ALL_PERMISSION_CODES
    if code
    not in {CAN_VIEW_USERS, CAN_MANAGE_USERS, CAN_VIEW_SECURITY, CAN_MANAGE_SECURITY}
)

ADMIN_GROUP_KEY = "admin"
STAFF_GROUP_KEY = "staff"
