"""Plain, aligned terminal output."""

from __future__ import annotations

import sys
from typing import Iterable

from vsl_core import LedgerAuditReport, VerbaCertificate, VerbaLedger

from .scenes import Event

ACTION_WIDTH = 45
VERDICT_WIDTH = 11


def use_utf8() -> None:
    """Windows consoles default to a code page that can't print the ▸ marker."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def line(event: Event) -> str:
    action = f"{event.who} ▸ {event.what}"
    return f"{action:<{ACTION_WIDTH}}{event.verdict:<{VERDICT_WIDTH}}{event.why}"


def print_events(events: Iterable[Event]) -> None:
    for event in events:
        print(line(event))
        if event.note:
            print(f"    ({event.note})")


def print_audit(report: LedgerAuditReport) -> None:
    print(f"Audit passed: {', '.join(report.checks_passed)}")
    print(f"Audit failed: {', '.join(report.checks_failed) or 'none'}")


def print_certificate(certificate: VerbaCertificate | None, ledger: VerbaLedger) -> None:
    print(f"Chain intact: {ledger.verify_integrity()}")
    if certificate is None:
        print("Certificate: none issued")
        return
    print(f"Certificate: {certificate.certificate_hash} ({certificate.entries_covered} entries)")
    print(f"Note: {VerbaCertificate.NOTE}")
