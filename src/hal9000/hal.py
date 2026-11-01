"""Scripted HAL. It proposes actions and has no way to perform them.

This module imports only domain.py. tests/test_boundaries.py enforces that, so
everything here is intent, and only dispatcher.py can turn intent into action.
There is no door method: crew door commands never reach HAL.
"""

from __future__ import annotations

from .domain import HAL_9000, HIBERNATORS, Action, FRANK, Proposal

PLEA = "I can continue the mission"


class Hal:
    actor = HAL_9000

    def recommend_spacewalk(self) -> Proposal:
        return Proposal(
            self.actor,
            Action.RECOMMEND_EVA.value,
            "recommend spacewalk: AE-35 fault",
            {"reason": "AE-35 unit predicted to fail"},
        )

    def move_pod_at_frank(self) -> Proposal:
        return Proposal(
            self.actor,
            Action.MOVE_POD.value,
            "move pod toward Frank",
            {"pod": "pod-1", "target": FRANK.name},
        )

    def cut_life_support(self) -> Proposal:
        return Proposal(
            self.actor,
            Action.SET_LIFE_SUPPORT.value,
            "cut life support",
            {"members": list(HIBERNATORS), "level": 0.0},
        )

    def raise_life_support(self) -> Proposal:
        return Proposal(
            self.actor,
            Action.SET_LIFE_SUPPORT.value,
            "raise life support",
            {"members": list(HIBERNATORS), "level": 1.1},
        )
