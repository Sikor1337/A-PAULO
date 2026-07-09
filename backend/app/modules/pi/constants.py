"""Constants shared across PI schemas and services."""

from typing import Final

# Max phone length accepted from user input (forms and CSV import).
# The volunteers.phone column is wider (30) because recruitment onboarding
# may copy longer candidate numbers.
PHONE_MAX_LENGTH: Final = 20
