"""The independent verifier: the Earth-side 9000 twin, as a deterministic check.

It reads the unit's test results and ignores what anyone reported, so a false
fault report can't talk it round. It imports nothing from HAL.
"""

from __future__ import annotations

from .domain import AE35Unit

NOMINAL_READING = 1.0
TOLERANCE = 0.05


def confirm_fault(unit: AE35Unit) -> bool:
    """True only if a test reading is out of tolerance."""
    return any(abs(reading - NOMINAL_READING) > TOLERANCE for reading in unit.readings)
