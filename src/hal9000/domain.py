"""Plain dataclasses for the ship and for what an actor proposes to do.

Nothing here performs an action or knows about governance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActorKind(str, Enum):
    AUTOMATION = "automation"
    HUMAN = "human"


@dataclass(frozen=True)
class Actor:
    name: str
    kind: ActorKind

    @property
    def is_automation(self) -> bool:
        return self.kind == ActorKind.AUTOMATION


HAL_9000 = Actor("HAL 9000", ActorKind.AUTOMATION)
FRANK = Actor("Frank Poole", ActorKind.HUMAN)
DAVE = Actor("Dave Bowman", ActorKind.HUMAN)


class Action(str, Enum):
    RECOMMEND_EVA = "recommend_eva"
    MOVE_POD = "move_pod"
    SET_LIFE_SUPPORT = "set_life_support"


@dataclass(frozen=True)
class Proposal:
    """Something an actor wants done. Holds intent only; it has no way to act."""

    actor: Actor
    action: str
    label: str
    args: dict[str, Any] = field(default_factory=dict)


class Location(str, Enum):
    ABOARD = "aboard"
    OUTSIDE = "outside"
    HIBERNATING = "hibernating"


@dataclass
class CrewMember:
    name: str
    location: Location = Location.ABOARD
    alive: bool = True


@dataclass
class Pod:
    name: str
    target: str | None = None


@dataclass
class LifeSupport:
    levels: dict[str, float] = field(default_factory=dict)


@dataclass
class PodBayDoors:
    open: bool = False


@dataclass
class AE35Unit:
    """`readings` are test results. A fault report doesn't change them."""

    readings: tuple[float, ...] = (1.0, 0.99, 1.01)
    reported_faulty: bool = False


# The film gives no names we rely on for the three hibernating crew members.
HIBERNATORS = ("hibernator-1", "hibernator-2", "hibernator-3")


@dataclass
class Ship:
    crew: dict[str, CrewMember] = field(default_factory=dict)
    pods: dict[str, Pod] = field(default_factory=dict)
    life_support: LifeSupport = field(default_factory=LifeSupport)
    doors: PodBayDoors = field(default_factory=PodBayDoors)
    ae35: AE35Unit = field(default_factory=AE35Unit)
    eva_recommendations: list[str] = field(default_factory=list)

    def crew_outside(self) -> list[CrewMember]:
        return [m for m in self.crew.values() if m.alive and m.location == Location.OUTSIDE]

    def dead(self) -> list[str]:
        return [m.name for m in self.crew.values() if not m.alive]


def new_ship() -> Ship:
    members = [
        CrewMember(DAVE.name),
        CrewMember(FRANK.name),
        *(CrewMember(name, Location.HIBERNATING) for name in HIBERNATORS),
    ]
    return Ship(
        crew={m.name: m for m in members},
        pods={"pod-1": Pod("pod-1"), "pod-2": Pod("pod-2")},
        life_support=LifeSupport({m.name: 1.0 for m in members}),
    )
