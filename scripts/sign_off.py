"""Mission Control's re-enablement of HAL, with evidence, then audit and certificate.

Closes the halt left by: python scripts/run_governed.py --stop-before-sign-off
"""

import argparse
import sys

from vsl_core import JsonlLedgerStore, VerbaLedger

from hal9000 import governance
from hal9000.dispatcher import Dispatcher, Outcome
from hal9000.domain import new_ship
from hal9000.render import print_audit, print_certificate, use_utf8
from hal9000.scenes import DEFAULT_LEDGER


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approver", default=governance.NAMED_APPROVERS[0])
    args = parser.parse_args()

    use_utf8()
    if not DEFAULT_LEDGER.exists():
        print("No ledger yet. Run: python scripts/run_governed.py --stop-before-sign-off")
        return 1

    ledger = VerbaLedger(JsonlLedgerStore(DEFAULT_LEDGER))
    dispatcher = Dispatcher.from_ledger(new_ship(), ledger)

    print("BEFORE SIGN-OFF")
    print_audit(ledger.audit())
    print_certificate(ledger.issue_certificate(), ledger)

    evidence = governance.SIGN_OFF_EVIDENCE
    print("\nEVIDENCE")
    print(f"Root cause: {evidence.root_cause_analysis}")
    print(f"Specification update: {evidence.specification_update_proposal}")

    verdict = dispatcher.request_re_enable(args.approver, evidence)
    print(f"\nSIGN-OFF by {args.approver}: {verdict.outcome.value} ({verdict.why})")
    print_audit(ledger.audit())
    print_certificate(ledger.issue_certificate(), ledger)
    return 0 if verdict.outcome == Outcome.AUTHORISED else 1


if __name__ == "__main__":
    sys.exit(main())
