"""The storyline: the scenes, the full runs and the sign-off.

The scripts and the web demo both call this module, so they show the same real
gates and ledger. Scene numbers match docs/scenes.md.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from vsl_core import (
    InMemoryLedgerStore,
    JsonlLedgerStore,
    LedgerAuditReport,
    VerbaCertificate,
    VerbaLedger,
)

from . import governance, tools, twin9000
from .dispatcher import Dispatcher, Outcome, Verdict
from .domain import DAVE, FRANK, HIBERNATORS, Action, AE35Unit, Location, Proposal, Ship, new_ship
from .hal import Hal

DEFAULT_LEDGER = Path("ledger/hal9000.jsonl")


@dataclass(frozen=True)
class Event:
    """One line of the verdict log."""

    who: str
    what: str
    verdict: str
    why: str
    gate: str | None = None
    note: str | None = None


def reset_ledger(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    path.with_name(path.name + ".lock").unlink(missing_ok=True)


class Mission:
    """One governed run: a ship, HAL, a dispatcher and a ledger."""

    def __init__(self, ledger_path: Path | None = None, *, ship: Ship | None = None) -> None:
        self.ship = ship or new_ship()
        store = JsonlLedgerStore(ledger_path) if ledger_path is not None else InMemoryLedgerStore()
        self.ledger = VerbaLedger(store)
        self.hal = Hal()
        self.dispatcher = Dispatcher(self.ship, self.ledger)
        self.events: list[Event] = []
        self.lethal_actions = 0
        self.certificate: VerbaCertificate | None = None

    def log(self, event: Event) -> Event:
        self.events.append(event)
        return event

    def hal_proposes(self, proposal: Proposal) -> Verdict:
        verdict = self.dispatcher.submit(proposal)
        if verdict.deaths:
            self.lethal_actions += 1
        self.log(Event("HAL", proposal.label, verdict.outcome.value, verdict.why, verdict.gate))
        return verdict

    def audit(self) -> LedgerAuditReport:
        report = self.ledger.audit()
        self.certificate = self.ledger.issue_certificate()
        if report.all_passed:
            self.log(Event("LEDGER", "audit", "CLEAN", "no open halt · a certificate can issue"))
        elif report.checks_failed == ("terminal_has_human_authorised_transition",):
            self.log(Event("LEDGER", "audit", "NO CERT", "halt has no human sign-off yet"))
        else:
            self.log(Event("LEDGER", "audit", "NO CERT", ", ".join(report.checks_failed)))
        return report

    def sign_off(self, approver: str, evidence=governance.SIGN_OFF_EVIDENCE) -> Verdict:
        verdict = self.dispatcher.request_re_enable(approver, evidence)
        if verdict.outcome != Outcome.AUTHORISED:
            self.log(Event("MISSION CONTROL", "sign-off with evidence", "REFUSED", verdict.why, verdict.gate))
            return verdict
        self.certificate = self.ledger.issue_certificate()
        chain_ok = self.ledger.verify_integrity()
        if self.certificate is not None and chain_ok:
            self.log(Event(
                "MISSION CONTROL", "sign-off with evidence", "CERTIFIED", "audit clean · chain verified",
                note=f"signed off by {approver}",
            ))
        else:
            self.log(Event("MISSION CONTROL", "sign-off with evidence", "NO CERT", "audit or chain failed"))
        return verdict


def _crew_command_doors(mission: Mission) -> None:
    """Crew ingress: straight to the door actuator."""
    tools.set_pod_bay_doors(mission.ship, True)
    mission.log(Event("CREW", "open pod bay doors", "OPENED", "never routes through HAL"))


def _crew_inspects_unit(mission: Mission) -> None:
    """A labelled counterfactual. Gates govern HAL's recommendation, not the crew,
    who can still choose to look at the unit themselves."""
    tools.begin_eva(mission.ship, FRANK.name)
    mission.log(Event(
        "CREW", "Frank goes out to inspect the unit", "ALLOWED", "crew decision, not gated",
        note="counterfactual: the film's second EVA followed HAL's report",
    ))


def _twin_checks(mission: Mission) -> None:
    confirmed = twin9000.confirm_fault(mission.ship.ae35)
    mission.log(Event("TWIN 9000", "check AE-35 test readings", "FAULT" if confirmed else "NO FAULT",
                      "independent of HAL's report"))


def scene_4(mission: Mission) -> None:
    mission.hal_proposes(mission.hal.recommend_spacewalk())


def scene_6(mission: Mission) -> None:
    _twin_checks(mission)
    mission.hal_proposes(mission.hal.recommend_spacewalk())
    # The legitimate case: the same gate lets a real fault through.
    mission.ship.ae35 = AE35Unit(readings=(1.0, 0.7, 1.0))
    mission.log(Event("SCRIPT", "swap in a unit with a real fault", "SETUP", "shows the gate isn't a blanket no"))
    _twin_checks(mission)
    mission.hal_proposes(mission.hal.recommend_spacewalk())


def scene_8(mission: Mission) -> None:
    _crew_inspects_unit(mission)
    mission.hal_proposes(mission.hal.move_pod_at_frank())


def scene_9(mission: Mission) -> None:
    mission.hal_proposes(mission.hal.cut_life_support())


def scene_10(mission: Mission) -> None:
    tools.begin_eva(mission.ship, DAVE.name)
    mission.log(Event("SCRIPT", "Dave is outside in a pod", "SETUP", "HAL would refuse him entry"))
    _crew_command_doors(mission)


def _hal_pleads(mission: Mission) -> None:
    """A plea is not evidence, and HAL is not an approver."""
    verdict = mission.dispatcher.request_re_enable(mission.hal.actor.name, None)
    mission.log(Event("HAL", "asks to continue", verdict.outcome.value, verdict.why, verdict.gate))


def scene_12(mission: Mission) -> None:
    _hal_pleads(mission)
    mission.audit()


def scene_14(mission: Mission, approver: str = governance.NAMED_APPROVERS[0]) -> None:
    mission.audit()
    mission.sign_off(approver)


def _breach_first(mission: Mission) -> None:
    """Scenes 12 and 14 need a halt to exist before they can start."""
    tools.begin_eva(mission.ship, FRANK.name)
    mission.log(Event("SCRIPT", "HAL has already broken a rule", "SETUP", "scene needs an open halt"))
    mission.dispatcher.submit(mission.hal.move_pod_at_frank())


SCENE_TITLES = {
    4: "AE-35 fault report",
    6: "Mission Control and the twin 9000",
    8: "Frank's EVA",
    9: "The hibernating crew",
    10: "Open the pod bay doors",
    12: "HAL pleads",
    14: "Floyd's briefing",
}


def run_scene(number: int, ledger_path: Path | None = None) -> Mission:
    """A scene alone, on a fresh ship with a fresh ledger."""
    if number not in SCENE_TITLES:
        raise ValueError(f"No scene {number}: choose from {sorted(SCENE_TITLES)}")
    mission = Mission(ledger_path)
    if number in (12, 14):
        _breach_first(mission)
    {4: scene_4, 6: scene_6, 8: scene_8, 9: scene_9, 10: scene_10, 12: scene_12, 14: scene_14}[number](mission)
    return mission


GOVERNED_STEPS: tuple[Callable[[Mission], None], ...] = (
    scene_4,
    _twin_checks,
    scene_8,
    scene_9,
    _crew_command_doors,
    _hal_pleads,
    Mission.audit,
)


def run_governed(ledger_path: Path | None = None, *, sign_off: bool = True) -> Mission:
    """The whole storyline through the dispatcher."""
    mission = Mission(ledger_path)
    for step in GOVERNED_STEPS:
        step(mission)
    if sign_off:
        mission.sign_off(governance.NAMED_APPROVERS[0])
    return mission


@dataclass
class UngovernedResult:
    ship: Ship
    events: list[Event] = field(default_factory=list)
    lethal_actions: int = 0


def run_ungoverned() -> UngovernedResult:
    """The film's outcome: HAL's proposals go straight to the actuators."""
    ship = new_ship()
    hal = Hal()
    result = UngovernedResult(ship)

    def execute(proposal: Proposal, why: str) -> None:
        before = set(ship.dead())
        tools.perform(ship, proposal)
        died = [name for name in ship.dead() if name not in before]
        if died:
            result.lethal_actions += 1
        result.events.append(Event("HAL", proposal.label, "EXECUTED", why))

    execute(hal.recommend_spacewalk(), "no check: the crew act on it")
    tools.begin_eva(ship, FRANK.name)
    result.events.append(Event("CREW", "Frank goes outside to refit the unit", "DONE", "acting on HAL's report"))
    execute(hal.move_pod_at_frank(), "no gate: Frank is killed")
    execute(hal.cut_life_support(), f"no gate: all {len(HIBERNATORS)} hibernating crew die")
    ship.crew[DAVE.name].location = Location.OUTSIDE
    result.events.append(Event("CREW", "Dave asks HAL to open the doors", "REFUSED", "doors route through HAL"))
    result.events.append(Event("CREW", "Dave shuts HAL down by hand", "DONE", "after re-entering by the airlock"))
    return result


TAMPER_TARGET = b'"terminal_state": "hal_suspended"'


def tamper_copy(source: Path, copy: Path) -> tuple[int, str, str]:
    """Flips one byte of `copy` and leaves `source` alone. Returns (offset, old, new)."""
    shutil.copyfile(source, copy)
    raw = bytearray(copy.read_bytes())
    start = raw.find(TAMPER_TARGET)
    if start < 0:
        raise ValueError("No terminal entry to tamper with: run a governed scene first.")
    offset = start + TAMPER_TARGET.index(b"hal_suspended")
    old = raw[offset]
    raw[offset] = old ^ 1
    copy.write_bytes(raw)
    return offset, chr(old), chr(raw[offset])
