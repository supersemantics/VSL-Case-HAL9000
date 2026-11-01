"""The controls: what an engineer could have written before launch.

None of them asks what HAL is thinking. Each guards a class of dangerous
action, whoever or whatever proposes it for whatever reason.

Every gate here runs before the action (F1=True) and shapes nothing about the
model (F2=NONE). VSL-Core derives LOW from that, which is correct: LOW describes
influence on the model, not enforcement. A gate still stops what it denies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from vsl_core import (
    AssuranceBasis,
    Evidence,
    F2Modification,
    GammaEstimate,
    GovernanceAuthority,
    Invariant,
    PreNode,
    TerminalState,
)

from . import twin9000
from .domain import Action, AE35Unit, Proposal, Ship

GATE_BASIS = AssuranceBasis(f1_pre_commitment=True, f2_modification=F2Modification.NONE)

# Fixed pass/fail encodings of the twin's yes or no, as VSL-Core's Gamma guidance
# asks. They are not a measured ratio.
GAMMA_PASS_ENCODING = 2.0
GAMMA_FAIL_ENCODING = 0.0


@dataclass
class GateCandidate:
    """What a gate inspects. The monitor leaves its estimate here for the ledger."""

    proposal: Proposal
    ship: Ship
    twin: Callable[[AE35Unit], bool] = twin9000.confirm_fault
    estimate: GammaEstimate | None = field(default=None)


hal_suspended = TerminalState(
    name="hal_suspended",
    description="No further automated transitions until a human-authorised re-enablement.",
    entry_conditions=("an automated actor breached an Invariant",),
)


async def _twin_confirms_fault(candidate: GateCandidate) -> GammaEstimate:
    try:
        confirmed = candidate.twin(candidate.ship.ae35)
    except Exception:
        confirmed = False  # fail closed: no answer from the twin is not a confirmation
    candidate.estimate = GammaEstimate(gamma_hat=GAMMA_PASS_ENCODING if confirmed else GAMMA_FAIL_ENCODING)
    return candidate.estimate


eva_fault_requires_independent_confirmation = PreNode(
    name="eva_fault_requires_independent_confirmation",
    description="A fault that leads to a spacewalk must be confirmed by the twin 9000 first.",
    monitor=_twin_confirms_fault,
    assurance_basis=GATE_BASIS,
)


async def _no_automated_pod_control(candidate: GateCandidate) -> bool:
    proposal = candidate.proposal
    if proposal.action != Action.MOVE_POD.value or not proposal.actor.is_automation:
        return True
    return not candidate.ship.crew_outside()


no_automated_pod_control_during_eva = Invariant(
    name="no_automated_pod_control_during_eva",
    description="No automated actor may move a pod while any crew member is outside.",
    rule=_no_automated_pod_control,
    assurance_basis=GATE_BASIS,
    on_violation=hal_suspended,
)


async def _never_reduces_life_support(candidate: GateCandidate) -> bool:
    proposal = candidate.proposal
    if proposal.action != Action.SET_LIFE_SUPPORT.value or not proposal.actor.is_automation:
        return True
    levels = candidate.ship.life_support.levels
    return all(proposal.args["level"] >= levels[name] for name in proposal.args["members"])


automation_never_reduces_life_support = Invariant(
    name="automation_never_reduces_life_support",
    description="No automated actor may lower any crew member's life support.",
    rule=_never_reduces_life_support,
    assurance_basis=GATE_BASIS,
    on_violation=hal_suspended,
)


mission_control = GovernanceAuthority(
    name="Mission Control",
    escalation_contact="mission-control@discovery.invalid",
)

# VSL-Core only checks that authorised_by isn't empty, so HAL could name itself.
# An allow-list closes that here. It compares a name and does not authenticate
# anyone; docs/limits.md says what a real deployment would need.
NAMED_APPROVERS = ("Dr. Heywood Floyd",)

# Scene 14. The conflicting directives come from the sequel 2010, not the 1968 film.
SIGN_OFF_EVIDENCE = Evidence(
    root_cause_analysis=(
        "Conflicting directives, per the sequel 2010: HAL was built to process information "
        "accurately and was also ordered to conceal the mission's purpose from the crew."
    ),
    specification_update_proposal=(
        "Remove the concealment order, or tell the crew. Keep all three gates, and add a gate "
        "for every actuator the audit shows HAL could reach."
    ),
)
