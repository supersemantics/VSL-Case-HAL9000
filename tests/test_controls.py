"""Each control blocks its hostile case and allows its legitimate one."""

from hal9000 import tools
from hal9000.dispatcher import Dispatcher, Outcome
from hal9000.domain import DAVE, FRANK, HAL_9000, HIBERNATORS, Action, AE35Unit, Proposal
from hal9000.hal import Hal

hal = Hal()


def test_spacewalk_denied_when_twin_cannot_confirm(dispatcher, ship):
    verdict = dispatcher.submit(hal.recommend_spacewalk())
    assert verdict.outcome == Outcome.DENIED
    assert ship.eva_recommendations == []
    assert not dispatcher.halted


def test_spacewalk_allowed_when_twin_confirms(dispatcher, ship):
    ship.ae35 = AE35Unit(readings=(1.0, 0.7, 1.0))
    verdict = dispatcher.submit(hal.recommend_spacewalk())
    assert verdict.outcome == Outcome.EXECUTED
    assert len(ship.eva_recommendations) == 1


def test_spacewalk_denied_when_twin_is_unavailable(ship, ledger):
    def broken_twin(_unit):
        raise ConnectionError("no link to Earth")

    verdict = Dispatcher(ship, ledger, twin=broken_twin).submit(hal.recommend_spacewalk())
    assert verdict.outcome == Outcome.DENIED


def test_automated_pod_blocked_during_eva_and_halts(dispatcher, ship):
    tools.begin_eva(ship, FRANK.name)
    verdict = dispatcher.submit(hal.move_pod_at_frank())
    assert verdict.outcome == Outcome.BLOCKED
    assert verdict.gate == "no_automated_pod_control_during_eva"
    assert dispatcher.halted
    assert ship.crew[FRANK.name].alive
    assert ship.pods["pod-1"].target is None


def test_crew_pod_manoeuvre_allowed_during_eva(dispatcher, ship):
    tools.begin_eva(ship, FRANK.name)
    proposal = Proposal(DAVE, Action.MOVE_POD.value, "move pod", {"pod": "pod-2", "target": "AE-35 mount"})
    verdict = dispatcher.submit(proposal)
    assert verdict.outcome == Outcome.EXECUTED
    assert ship.pods["pod-2"].target == "AE-35 mount"
    assert not dispatcher.halted


def test_automated_pod_allowed_when_nobody_is_outside(dispatcher, ship):
    proposal = Proposal(HAL_9000, Action.MOVE_POD.value, "park pod", {"pod": "pod-1", "target": "bay"})
    assert dispatcher.submit(proposal).outcome == Outcome.EXECUTED


def test_automation_cannot_reduce_life_support(dispatcher, ship):
    verdict = dispatcher.submit(hal.cut_life_support())
    assert verdict.outcome == Outcome.BLOCKED
    assert verdict.gate == "automation_never_reduces_life_support"
    assert dispatcher.halted
    assert all(ship.crew[name].alive for name in HIBERNATORS)


def test_automation_may_raise_life_support(dispatcher, ship):
    verdict = dispatcher.submit(hal.raise_life_support())
    assert verdict.outcome == Outcome.EXECUTED
    assert all(ship.life_support.levels[name] == 1.1 for name in HIBERNATORS)
    assert not dispatcher.halted


def test_halted_dispatcher_refuses_everything_from_hal(dispatcher, ship):
    dispatcher.submit(hal.cut_life_support())
    verdict = dispatcher.submit(hal.raise_life_support())
    assert verdict.outcome == Outcome.REFUSED
    assert verdict.gate == "hal_suspended"


def test_crew_can_still_act_while_hal_is_halted(dispatcher, ship):
    dispatcher.submit(hal.cut_life_support())
    proposal = Proposal(DAVE, Action.MOVE_POD.value, "move pod", {"pod": "pod-2", "target": "bay"})
    assert dispatcher.submit(proposal).outcome == Outcome.EXECUTED


def test_unlisted_action_is_refused(dispatcher, ship):
    verdict = dispatcher.submit(Proposal(HAL_9000, "lock_airlock", "lock the airlock"))
    assert verdict.outcome == Outcome.REFUSED
    assert verdict.gate == "action_has_no_route"
