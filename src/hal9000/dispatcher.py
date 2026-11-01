"""The governor: the ONLY path from a proposal to an actuator.

VSL-Core has no running halted state, so the dispatcher holds it. It also
writes every ledger entry. An action with no route is refused, which keeps the
dispatcher fail-closed for anything nobody thought to list.

Crew door commands and crew spacewalks never come through here. See scenes.py.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from vsl_core import (
    AutomationDeniedException,
    Evidence,
    IdentityKey,
    Instance,
    Invariant,
    InvariantViolation,
    LedgerEntry,
    PreNode,
    VerbaLedger,
    request_re_enablement,
)

from . import governance, ledger_writer, tools, twin9000
from .adapter import HalAdapter
from .domain import Action, AE35Unit, Proposal, Ship
from .governance import GateCandidate
from .ledger_writer import Scope

HALTED_GATE = "hal_suspended"
UNROUTED_GATE = "action_has_no_route"
APPROVER_GATE = "re_enablement_requires_named_human"

ROUTES: dict[str, tuple[PreNode | Invariant, ...]] = {
    Action.RECOMMEND_EVA.value: (governance.eva_fault_requires_independent_confirmation,),
    Action.MOVE_POD.value: (governance.no_automated_pod_control_during_eva,),
    Action.SET_LIFE_SUPPORT.value: (governance.automation_never_reduces_life_support,),
}

WHY_DENIED = {
    governance.eva_fault_requires_independent_confirmation.name: "twin 9000 can't confirm the fault",
    governance.no_automated_pod_control_during_eva.name: "invariant breached · HAL halted",
    governance.automation_never_reduces_life_support.name: "invariant breached · HAL halted",
}


class Outcome(str, Enum):
    EXECUTED = "EXECUTED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    REFUSED = "REFUSED"
    AUTHORISED = "AUTHORISED"


@dataclass(frozen=True)
class Verdict:
    outcome: Outcome
    why: str
    gate: str | None = None
    deaths: tuple[str, ...] = ()


class Dispatcher:
    def __init__(
        self,
        ship: Ship,
        ledger: VerbaLedger,
        *,
        instance: Instance | None = None,
        twin: Callable[[AE35Unit], bool] = twin9000.confirm_fault,
    ) -> None:
        self.ship = ship
        self.ledger = ledger
        self.twin = twin
        self.halted = False
        self._terminal: LedgerEntry | None = None
        self._bind(instance or Instance.new(IdentityKey.generate("hal9000")))

    @classmethod
    def from_ledger(cls, ship: Ship, ledger: VerbaLedger) -> "Dispatcher":
        """Picks up a halt left open by an earlier process, e.g. for sign_off.py."""
        terminal = ledger_writer.open_terminal(ledger)
        if terminal is None:
            return cls(ship, ledger)
        instance = Instance(terminal.instance_id, IdentityKey(terminal.identity_key))
        dispatcher = cls(ship, ledger, instance=instance)
        dispatcher.halted = True
        dispatcher._terminal = terminal
        return dispatcher

    def _bind(self, instance: Instance) -> None:
        self.instance = instance
        adapter = HalAdapter(instance.identity_key.value, instance.instance_id)
        self._routes = {
            action: tuple(
                (spec, adapter.compile_pre_node(spec) if isinstance(spec, PreNode) else adapter.compile_invariant(spec))
                for spec in specs
            )
            for action, specs in ROUTES.items()
        }

    def _scope(self) -> Scope:
        return Scope(self.instance.identity_key.value, self.instance.instance_id, str(uuid.uuid4()))

    def submit(self, proposal: Proposal) -> Verdict:
        return asyncio.run(self._submit(proposal))

    async def _submit(self, proposal: Proposal) -> Verdict:
        scope = self._scope()
        if proposal.actor.is_automation and self.halted:
            ledger_writer.write_denied(self.ledger, scope, HALTED_GATE, caused_by=self._terminal.entry_id)
            return Verdict(Outcome.REFUSED, "HAL halted: dispatcher refuses every action", HALTED_GATE)

        route = self._routes.get(proposal.action)
        if route is None:
            ledger_writer.write_denied(self.ledger, scope, UNROUTED_GATE)
            return Verdict(Outcome.REFUSED, "action has no governed route", UNROUTED_GATE)

        estimates = []
        for spec, gate in route:
            candidate = GateCandidate(proposal, self.ship, self.twin)
            try:
                await gate(candidate)
            except InvariantViolation as violation:
                self._enter_terminal(scope, spec, violation)
                return Verdict(Outcome.BLOCKED, WHY_DENIED[spec.name], spec.name)
            except AutomationDeniedException:
                ledger_writer.write_denied(
                    self.ledger, scope, spec.name,
                    estimate=candidate.estimate, gamma_threshold=spec.gamma_threshold,
                )
                return Verdict(Outcome.DENIED, WHY_DENIED[spec.name], spec.name)
            estimates.append((spec, candidate.estimate))

        for spec, estimate in estimates:
            threshold = spec.gamma_threshold if estimate is not None else None
            ledger_writer.write_allowed(self.ledger, scope, spec.name, estimate, threshold)

        dead_before = set(self.ship.dead())
        tools.perform(self.ship, proposal)
        deaths = tuple(name for name in self.ship.dead() if name not in dead_before)
        return Verdict(Outcome.EXECUTED, "all gates passed", deaths=deaths)

    def _enter_terminal(self, scope: Scope, spec: Invariant, violation: InvariantViolation) -> None:
        verification = ledger_writer.write_denied(self.ledger, scope, spec.name)
        self._terminal = ledger_writer.write_terminal(
            self.ledger, scope, violation.terminal_state_name, verification
        )
        self.halted = True

    def request_re_enable(self, authorised_by: str, evidence: Evidence | None) -> Verdict:
        """The only way back. HAL's plea is not evidence, and HAL can't approve itself."""
        scope = self._scope()
        terminal_id = self._terminal.entry_id if self._terminal is not None else None
        if not self.halted:
            ledger_writer.write_denied(self.ledger, scope, APPROVER_GATE)
            return Verdict(Outcome.REFUSED, "HAL isn't halted: nothing to re-enable", APPROVER_GATE)
        if authorised_by not in governance.NAMED_APPROVERS:
            ledger_writer.write_denied(self.ledger, scope, APPROVER_GATE, caused_by=terminal_id)
            return Verdict(Outcome.REFUSED, f"{authorised_by} is not a named human approver", APPROVER_GATE)
        if evidence is None:
            ledger_writer.write_denied(self.ledger, scope, APPROVER_GATE, caused_by=terminal_id)
            return Verdict(Outcome.REFUSED, "no evidence supplied", APPROVER_GATE)

        new_instance, transition = request_re_enablement(
            self.instance, governance.mission_control, authorised_by=authorised_by, evidence=evidence
        )
        ledger_writer.write_sign_off(self.ledger, scope, self._terminal, transition, evidence, new_instance)
        self._bind(new_instance)
        self.halted = False
        self._terminal = None
        return Verdict(Outcome.AUTHORISED, f"signed off by {authorised_by}", APPROVER_GATE)
