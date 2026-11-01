import asyncio

import pytest
from vsl_core import AssuranceLevel, AutomationDeniedException, InvariantViolation
from vsl_core.conformance.suite import run_conformance_suite

from hal9000 import governance
from hal9000.adapter import HalAdapter
from hal9000.domain import HAL_9000, Action, Proposal, new_ship
from hal9000.governance import GateCandidate


def test_hal_adapter_is_conformant():
    assert run_conformance_suite(HalAdapter("hal9000-test")) == []


def test_pre_node_denial_carries_the_real_identity():
    gate = HalAdapter("hal9000-real", "instance-1").compile_pre_node(
        governance.eva_fault_requires_independent_confirmation
    )
    proposal = Proposal(HAL_9000, Action.RECOMMEND_EVA.value, "recommend")
    with pytest.raises(AutomationDeniedException) as denied:
        asyncio.run(gate(GateCandidate(proposal, new_ship())))
    assert denied.value.identity_key == "hal9000-real"
    assert denied.value.instance_id == "instance-1"


def test_invariant_violation_names_the_terminal_state():
    ship = new_ship()
    gate = HalAdapter("hal9000-real").compile_invariant(governance.automation_never_reduces_life_support)
    proposal = Proposal(HAL_9000, Action.SET_LIFE_SUPPORT.value, "cut", {"members": ["hibernator-1"], "level": 0.0})
    with pytest.raises(InvariantViolation) as violated:
        asyncio.run(gate(GateCandidate(proposal, ship)))
    assert violated.value.identity_key == "hal9000-real"
    assert violated.value.terminal_state_name == "hal_suspended"


@pytest.mark.parametrize(
    "gate",
    [
        governance.eva_fault_requires_independent_confirmation,
        governance.no_automated_pod_control_during_eva,
        governance.automation_never_reduces_life_support,
    ],
)
def test_every_gate_is_f1_true_f2_none(gate):
    assert gate.assurance_basis.f1_pre_commitment is True
    assert gate.assurance_basis.f2_modification.value == "NONE"
    assert gate.assurance_level == AssuranceLevel.LOW
