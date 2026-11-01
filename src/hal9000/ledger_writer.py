"""The standard entry chain. VSL-Core's ledger doesn't write itself.

Denied gate:   MONITOR -> PRE_NODE -> VERIFICATION -> SPECIFICATION_UPDATE
Terminal:      ... VERIFICATION -> TERMINAL
Refused while halted: the denied chain again, caused by the TERMINAL, with no
second TERMINAL.
Sign-off:      TERMINAL -> HUMAN_AUTHORISED_TRANSITION -> RE_ENABLEMENT
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vsl_core import (
    Evidence,
    HumanAuthorisedTransition,
    Instance,
    LedgerEntry,
    LedgerEntryType,
    VerbaLedger,
    VerificationResult,
)


@dataclass(frozen=True)
class Scope:
    """Who a run of entries belongs to, and which decision groups them."""

    identity_key: str
    instance_id: str
    decision_id: str

    def fields(self) -> dict[str, Any]:
        return {
            "identity_key": self.identity_key,
            "instance_id": self.instance_id,
            "decision_id": self.decision_id,
        }


def write_allowed(ledger: VerbaLedger, scope: Scope, gate: str, estimate=None, gamma_threshold=None) -> LedgerEntry:
    if estimate is not None:
        return ledger.write_gate_decision(
            primitive_name=gate, estimate=estimate, gamma_threshold=gamma_threshold, **scope.fields()
        )
    return ledger.write_gate_decision(primitive_name=gate, allowed=True, **scope.fields())


def write_denied(
    ledger: VerbaLedger,
    scope: Scope,
    gate: str,
    *,
    estimate=None,
    gamma_threshold=None,
    caused_by: str | None = None,
) -> LedgerEntry:
    """Writes the four-entry denied chain and returns its VERIFICATION entry."""
    if estimate is not None:
        monitor = ledger.write_gate_decision(
            primitive_name=gate, estimate=estimate, gamma_threshold=gamma_threshold,
            caused_by=caused_by, **scope.fields(),
        )
    else:
        monitor = ledger.write_gate_decision(
            primitive_name=gate, allowed=False, caused_by=caused_by, **scope.fields()
        )
    pre_node = ledger.write(
        LedgerEntryType.PRE_NODE,
        caused_by=monitor.entry_id,
        payload={"gate": gate, "outcome": "denied"},
        **scope.fields(),
    )
    verification = ledger.write_verification(
        result=VerificationResult.INSUFFICIENT, caused_by=pre_node.entry_id, **scope.fields()
    )
    ledger.write(
        LedgerEntryType.SPECIFICATION_UPDATE,
        caused_by=verification.entry_id,
        payload={"note": "escalated to Mission Control"},
        **scope.fields(),
    )
    return verification


def write_terminal(ledger: VerbaLedger, scope: Scope, terminal_state: str, verification: LedgerEntry) -> LedgerEntry:
    return ledger.write(
        LedgerEntryType.TERMINAL,
        caused_by=verification.entry_id,
        payload={"terminal_state": terminal_state},
        **scope.fields(),
    )


def write_sign_off(
    ledger: VerbaLedger,
    scope: Scope,
    terminal: LedgerEntry,
    transition: HumanAuthorisedTransition,
    evidence: Evidence,
    new_instance: Instance,
) -> LedgerEntry:
    approval = ledger.write(
        LedgerEntryType.HUMAN_AUTHORISED_TRANSITION,
        caused_by=terminal.entry_id,
        payload={
            "authorised_by": transition.authorised_by,
            "authority": transition.authority.name,
            "authorisation_evidence_hash": transition.authorisation_evidence_hash,
            "evidence": {
                "root_cause_analysis": evidence.root_cause_analysis,
                "specification_update_proposal": evidence.specification_update_proposal,
            },
        },
        **scope.fields(),
    )
    return ledger.write(
        LedgerEntryType.RE_ENABLEMENT,
        identity_key=new_instance.identity_key.value,
        instance_id=new_instance.instance_id,
        decision_id=scope.decision_id,
        caused_by=approval.entry_id,
        payload={"predecessor_instance_id": new_instance.predecessor_instance_id},
    )


def open_terminal(ledger: VerbaLedger) -> LedgerEntry | None:
    """The latest TERMINAL with no human-authorised transition, if any."""
    entries = list(ledger.store.all_entries())
    approved = {e.caused_by for e in entries if e.entry_type == LedgerEntryType.HUMAN_AUTHORISED_TRANSITION}
    terminals = [e for e in entries if e.entry_type == LedgerEntryType.TERMINAL and e.entry_id not in approved]
    return terminals[-1] if terminals else None
