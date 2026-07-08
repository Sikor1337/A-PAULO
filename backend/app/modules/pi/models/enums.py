"""Status enums for PI domain models — single source of allowed values."""

from enum import StrEnum


class VolunteerStatus(StrEnum):
    AKTYWNY = "Aktywny"
    BYLY = "Były"


class BeneficiaryStatus(StrEnum):
    OBECNY = "OBECNY"
    ZMARLY = "ZMARŁY"
    BYLY = "BYŁY"
    DPS_ZOL = "DPS_ZOL"
