"""HalAdapter: a VSLAdapter that raises with the real identity.

VSL-Core's PlainPythonReferenceAdapter hard-codes identity_key="conformance-test"
in its exceptions, so its denials can't be traced to an agent. See
docs/upstream-notes.md. Fallback is left declarative, as it is there: a gate
checks once and does not retry.
"""

from __future__ import annotations

from typing import Any

from vsl_core import AutomationDeniedException, Invariant, InvariantViolation, PreNode
from vsl_core.conformance.protocol import CompiledGate


class HalAdapter:
    def __init__(self, identity_key: str, instance_id: str | None = None) -> None:
        self.identity_key = identity_key
        self.instance_id = instance_id

    def compile_pre_node(self, pre_node: PreNode) -> CompiledGate:
        async def gate(candidate_input: Any) -> None:
            estimate = await pre_node.monitor(candidate_input)
            if not estimate.sufficient(pre_node.gamma_threshold):
                raise AutomationDeniedException(
                    reason=f"Pre-node '{pre_node.name}' insufficient Gamma",
                    identity_key=self.identity_key,
                    instance_id=self.instance_id,
                )

        return gate

    def compile_invariant(self, invariant: Invariant) -> CompiledGate:
        async def gate(candidate_input: Any) -> None:
            if await invariant.rule(candidate_input):
                return
            reason = f"Invariant '{invariant.name}' violated"
            terminal = invariant.on_violation.name if invariant.on_violation is not None else None
            if terminal is not None:
                reason += f" -- entering terminal state '{terminal}'"
            raise InvariantViolation(
                reason=reason,
                identity_key=self.identity_key,
                instance_id=self.instance_id,
                invariant_name=invariant.name,
                terminal_state_name=terminal,
            )

        return gate
