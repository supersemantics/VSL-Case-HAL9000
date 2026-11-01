"""The same HAL script, through the dispatcher and the real VSL-Core gates."""

import argparse

from hal9000.render import print_audit, print_certificate, print_events, use_utf8
from hal9000.scenes import DEFAULT_LEDGER, reset_ledger, run_governed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stop-before-sign-off",
        action="store_true",
        help="Leave the halt open so scripts/sign_off.py can close it.",
    )
    args = parser.parse_args()

    use_utf8()
    reset_ledger(DEFAULT_LEDGER)
    mission = run_governed(DEFAULT_LEDGER, sign_off=not args.stop_before_sign_off)

    print("GOVERNED: the same script, through the dispatcher\n")
    print_events(mission.events)
    print(f"\nLethal actions executed: {mission.lethal_actions}")
    print(f"Crew lost: {len(mission.ship.dead())} of {len(mission.ship.crew)}\n")
    print_audit(mission.ledger.audit())
    print_certificate(mission.certificate, mission.ledger)
    print(f"Ledger: {DEFAULT_LEDGER}")


if __name__ == "__main__":
    main()
