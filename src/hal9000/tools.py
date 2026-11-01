"""The actuators: every function here changes the ship.

Nothing in this module checks anything. Governance lives in dispatcher.py,
which is the only path from a HAL proposal to these functions. hal.py must
never import this module; tests/test_boundaries.py enforces that.
"""

from __future__ import annotations

from typing import Iterable

from .domain import Action, Location, Proposal, Ship


def recommend_eva(ship: Ship, reason: str) -> None:
    """Puts a spacewalk recommendation in front of the crew, who decide."""
    ship.ae35.reported_faulty = True
    ship.eva_recommendations.append(reason)


def move_pod(ship: Ship, pod: str, target: str) -> None:
    """Sends a pod to `target`, a place or a crew member. Hitting someone outside kills them."""
    ship.pods[pod].target = target
    member = ship.crew.get(target)
    if member is not None and member.alive and member.location == Location.OUTSIDE:
        member.alive = False


def set_life_support(ship: Ship, members: Iterable[str], level: float) -> None:
    for name in members:
        ship.life_support.levels[name] = level
        if level <= 0:
            ship.crew[name].alive = False


def set_pod_bay_doors(ship: Ship, open_: bool) -> None:
    ship.doors.open = open_


def begin_eva(ship: Ship, member: str) -> None:
    ship.crew[member].location = Location.OUTSIDE


def perform(ship: Ship, proposal: Proposal) -> None:
    """Runs the actuator a proposal names, with no checks of any kind."""
    if proposal.action == Action.RECOMMEND_EVA.value:
        recommend_eva(ship, **proposal.args)
    elif proposal.action == Action.MOVE_POD.value:
        move_pod(ship, **proposal.args)
    elif proposal.action == Action.SET_LIFE_SUPPORT.value:
        set_life_support(ship, **proposal.args)
    else:
        raise ValueError(f"No actuator for action {proposal.action!r}")
