"""Beneficiary recruitment defaults and public-link constants (PAP-90)."""

BENEFICIARY_RECRUITMENT_ROUTE_PREFIX = "/beneficiary-application"
BENEFICIARY_RECRUITMENT_TOKEN_HEADER = "X-Beneficiary-Recruitment-Token"

BENEFICIARY_RECRUITMENT_STATUSES = {
    "NEW",
    "BENEFICIARY_CREATED",
    "REJECTED",
    "ARCHIVED",
}
