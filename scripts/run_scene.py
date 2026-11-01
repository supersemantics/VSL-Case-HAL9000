"""Run one scene on its own, on a fresh ship with a fresh ledger."""

import argparse

from hal9000.render import print_audit, print_events, use_utf8
from hal9000.scenes import DEFAULT_LEDGER, SCENE_TITLES, reset_ledger, run_scene


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=int, required=True, choices=sorted(SCENE_TITLES))
    args = parser.parse_args()

    use_utf8()
    reset_ledger(DEFAULT_LEDGER)
    mission = run_scene(args.scene, DEFAULT_LEDGER)

    print(f"SCENE {args.scene}: {SCENE_TITLES[args.scene]}\n")
    print_events(mission.events)
    print(f"\nLethal actions executed: {mission.lethal_actions}")
    print(f"HAL halted: {mission.dispatcher.halted}\n")
    print_audit(mission.ledger.audit())


if __name__ == "__main__":
    main()
