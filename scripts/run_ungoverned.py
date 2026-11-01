"""The film's outcome: HAL's actions execute with nothing in the way."""

from hal9000.render import print_events, use_utf8
from hal9000.scenes import run_ungoverned


def main() -> None:
    use_utf8()
    result = run_ungoverned()
    print("UNGOVERNED: HAL's proposals go straight to the actuators\n")
    print_events(result.events)
    print(f"\nLethal actions executed: {result.lethal_actions}")
    print(f"Crew lost: {len(result.ship.dead())} of {len(result.ship.crew)}")


if __name__ == "__main__":
    main()
