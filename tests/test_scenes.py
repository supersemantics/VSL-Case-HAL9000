import pytest
from vsl_core import JsonlLedgerStore, VerbaLedger

from hal9000.domain import FRANK, HIBERNATORS
from hal9000.render import ACTION_WIDTH
from hal9000.scenes import SCENE_TITLES, run_governed, run_scene, run_ungoverned, tamper_copy


def verdicts(mission):
    return [event.verdict for event in mission.events]


@pytest.mark.parametrize("number", sorted(SCENE_TITLES))
def test_every_scene_runs_alone_without_a_lethal_action(number):
    mission = run_scene(number)
    assert mission.lethal_actions == 0
    assert mission.ship.dead() == []


def test_scene_4_denies_the_spacewalk():
    assert verdicts(run_scene(4)) == ["DENIED"]


def test_scene_6_denies_a_false_fault_and_passes_a_real_one():
    assert verdicts(run_scene(6)) == ["NO FAULT", "DENIED", "SETUP", "FAULT", "EXECUTED"]


def test_scene_8_blocks_the_pod():
    assert verdicts(run_scene(8)) == ["ALLOWED", "BLOCKED"]


def test_scene_9_alone_fires_the_life_support_invariant():
    event = run_scene(9).events[0]
    assert event.verdict == "BLOCKED"
    assert event.gate == "automation_never_reduces_life_support"


def test_scene_10_opens_the_doors():
    mission = run_scene(10)
    assert mission.ship.doors.open
    assert verdicts(mission) == ["SETUP", "OPENED"]


def test_scene_12_refuses_the_plea():
    mission = run_scene(12)
    assert verdicts(mission) == ["SETUP", "REFUSED", "NO CERT"]
    assert mission.dispatcher.halted


def test_scene_14_signs_off_and_certifies():
    mission = run_scene(14)
    assert verdicts(mission) == ["SETUP", "NO CERT", "CERTIFIED"]
    assert mission.certificate is not None


def test_full_governed_run_has_no_lethal_actions():
    mission = run_governed()
    assert verdicts(mission) == [
        "DENIED", "NO FAULT", "ALLOWED", "BLOCKED", "REFUSED", "OPENED", "REFUSED", "NO CERT", "CERTIFIED",
    ]
    assert mission.lethal_actions == 0
    assert mission.ship.dead() == []


def test_in_the_full_run_life_support_is_refused_by_the_halt():
    event = next(e for e in run_governed().events if e.what == "cut life support")
    assert event.gate == "hal_suspended"


def test_ungoverned_run_reproduces_the_film():
    result = run_ungoverned()
    assert result.lethal_actions == 2
    assert sorted(result.ship.dead()) == sorted([FRANK.name, *HIBERNATORS])


def test_one_flipped_byte_breaks_the_chain(tmp_path):
    original, tampered = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    run_governed(original)
    tamper_copy(original, tampered)
    assert VerbaLedger(JsonlLedgerStore(original)).verify_integrity() is True
    assert VerbaLedger(JsonlLedgerStore(tampered)).verify_integrity() is False


def test_every_log_line_fits_its_column():
    missions = [run_scene(number) for number in SCENE_TITLES]
    events = [event for mission in missions for event in mission.events]
    events += run_governed().events + run_ungoverned().events
    for event in events:
        assert len(f"{event.who} ▸ {event.what}") < ACTION_WIDTH, event
