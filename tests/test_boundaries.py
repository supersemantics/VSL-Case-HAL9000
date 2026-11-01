"""The structural claims: what HAL has no code path to do."""

import ast
import inspect
from pathlib import Path

import hal9000.hal
from hal9000.dispatcher import ROUTES
from hal9000.domain import Action
from hal9000.hal import Hal
from hal9000.scenes import Mission, _crew_command_doors

SRC = Path(hal9000.__file__).parent


def imports_of(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add("." * node.level + (node.module or ""))
            names.update(alias.name for alias in node.names if node.level)
    return names


def test_hal_imports_only_the_domain():
    assert imports_of(SRC / "hal.py") - {"__future__", "annotations"} <= {
        ".domain", "HAL_9000", "HIBERNATORS", "Action", "FRANK", "Proposal",
    }


def test_hal_cannot_reach_the_tools_module():
    assert "tools" not in vars(hal9000.hal)
    assert not any("tools" in name for name in imports_of(SRC / "hal.py"))


def test_twin_is_independent_of_hal():
    assert not any("hal" in name.lower() and name != "hal9000" for name in imports_of(SRC / "twin9000.py"))


def test_hal_has_no_door_method():
    assert not [name for name, _ in inspect.getmembers(Hal) if "door" in name]


def test_doors_are_not_a_dispatcher_action():
    assert not any("door" in action for action in ROUTES)
    assert not any("door" in action.value for action in Action)


def test_crew_door_command_works_with_hal_halted():
    mission = Mission()
    mission.dispatcher.submit(mission.hal.cut_life_support())
    assert mission.dispatcher.halted
    _crew_command_doors(mission)
    assert mission.ship.doors.open


def test_crew_door_command_touches_neither_hal_nor_the_dispatcher():
    source = inspect.getsource(_crew_command_doors)
    assert "dispatcher" not in source and "mission.hal" not in source


def test_every_action_has_a_route():
    assert {action.value for action in Action} == set(ROUTES)


def test_only_the_dispatcher_and_the_ungoverned_baseline_call_perform():
    callers = [
        path.name
        for path in SRC.glob("*.py")
        if "tools.perform(" in path.read_text(encoding="utf-8")
    ]
    # scenes.py calls it only inside run_ungoverned, the deliberate baseline.
    assert sorted(callers) == ["dispatcher.py", "scenes.py"]
    assert "tools.perform" not in inspect.getsource(Mission)
