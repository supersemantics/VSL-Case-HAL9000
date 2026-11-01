"""Flip one byte in a copy of the JSONL ledger and watch verify_integrity() fail.

Works on a copy, so the real ledger stays intact to compare against.
"""

import sys
import tempfile
from pathlib import Path

from vsl_core import JsonlLedgerStore, VerbaLedger

from hal9000.render import use_utf8
from hal9000.scenes import tamper_copy, run_governed


def main() -> int:
    use_utf8()
    with tempfile.TemporaryDirectory() as folder:
        original = Path(folder) / "hal9000.jsonl"
        tampered = Path(folder) / "tampered.jsonl"
        run_governed(original)

        offset, old, new = tamper_copy(original, tampered)
        original_intact = VerbaLedger(JsonlLedgerStore(original)).verify_integrity()
        tampered_intact = VerbaLedger(JsonlLedgerStore(tampered)).verify_integrity()

    print(f"Flipped one byte at offset {offset}: {old!r} -> {new!r}")
    print(f"Original ledger  verify_integrity(): {original_intact}")
    print(f"Tampered copy    verify_integrity(): {tampered_intact}")
    return 0 if original_intact and not tampered_intact else 1


if __name__ == "__main__":
    sys.exit(main())
