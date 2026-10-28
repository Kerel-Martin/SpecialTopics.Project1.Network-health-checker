"""Validate candidate IPv4 addresses (requirement R2)."""

import ipaddress
from dataclasses import dataclass

VALID = "VALID"
INVALID = "INVALID"


@dataclass(frozen=True)
class Entry:
    """One input line and the result of validating it."""

    text: str
    status: str  # VALID or INVALID
    reason: str = ""

    @property
    def is_valid(self):
        return self.status == VALID


def validate_entry(text):
    """Return an Entry saying whether ``text`` is a valid IPv4 address.

    Python's ``ipaddress`` module does the check. It rejects octets above
    255, the wrong number of octets, letters, and leading zeros such as
    ``192.168.01.1``.
    """
    try:
        ipaddress.IPv4Address(text)
    except ValueError as error:
        return Entry(text, INVALID, str(error))
    return Entry(text, VALID)


def validate_entries(texts):
    """Validate every text in ``texts`` and return a list of Entry objects."""
    return [validate_entry(text) for text in texts]


def count_summary(entries):
    """Return the input, valid and invalid counts for ``entries``."""
    valid = sum(1 for entry in entries if entry.is_valid)
    return {
        "input_entries": len(entries),
        "valid": valid,
        "invalid": len(entries) - valid,
    }
