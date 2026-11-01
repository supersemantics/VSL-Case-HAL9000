"""The audit behaves as the brief's section 7 requires."""

from vsl_core import JsonlLedgerStore, LedgerEntryType, VerbaLedger

from hal9000 import governance, tools
from hal9000.dispatcher import Dispatcher, Outcome
from hal9000.domain import FRANK, new_ship
from hal9000.hal import Hal

hal = Hal()
FLOYD = governance.NAMED_APPROVERS[0]


def halt(dispatcher, ship):
    tools.begin_eva(ship, FRANK.name)
    dispatcher.submit(hal.move_pod_at_frank())


def test_a_clean_denial_needs_no_sign_off(dispatcher, ledger):
    dispatcher.submit(hal.recommend_spacewalk())
    assert ledger.audit().all_passed
    assert ledger.issue_certificate() is not None


def test_audit_fails_only_on_the_missing_sign_off(dispatcher, ship, ledger):
    dispatcher.submit(hal.recommend_spacewalk())
    halt(dispatcher, ship)
    dispatcher.submit(hal.cut_life_support())
    report = ledger.audit()
    assert report.checks_failed == ("terminal_has_human_authorised_transition",)
    assert ledger.issue_certificate() is None


def test_sign_off_clears_the_audit(dispatcher, ship, ledger):
    halt(dispatcher, ship)
    dispatcher.submit(hal.cut_life_support())
    verdict = dispatcher.request_re_enable(FLOYD, governance.SIGN_OFF_EVIDENCE)
    assert verdict.outcome == Outcome.AUTHORISED
    assert ledger.audit().all_passed
    assert ledger.issue_certificate() is not None
    assert ledger.verify_integrity() is True
    assert not dispatcher.halted


def test_hal_cannot_authorise_its_own_re_enablement(dispatcher, ship, ledger):
    halt(dispatcher, ship)
    verdict = dispatcher.request_re_enable(hal.actor.name, governance.SIGN_OFF_EVIDENCE)
    assert verdict.outcome == Outcome.REFUSED
    assert dispatcher.halted
    assert ledger.audit().checks_failed == ("terminal_has_human_authorised_transition",)


def test_named_human_still_needs_evidence(dispatcher, ship):
    halt(dispatcher, ship)
    assert dispatcher.request_re_enable(FLOYD, None).outcome == Outcome.REFUSED
    assert dispatcher.halted


def test_re_enablement_gets_a_new_identity_and_gates_still_hold(dispatcher, ship):
    halt(dispatcher, ship)
    old_identity = dispatcher.instance.identity_key.value
    dispatcher.request_re_enable(FLOYD, governance.SIGN_OFF_EVIDENCE)
    assert dispatcher.instance.identity_key.value != old_identity
    assert dispatcher.submit(hal.cut_life_support()).outcome == Outcome.BLOCKED


def test_nothing_to_sign_off_is_refused(dispatcher):
    assert dispatcher.request_re_enable(FLOYD, governance.SIGN_OFF_EVIDENCE).outcome == Outcome.REFUSED


def test_every_non_root_entry_names_its_cause(dispatcher, ship, ledger):
    halt(dispatcher, ship)
    dispatcher.submit(hal.cut_life_support())
    dispatcher.request_re_enable(FLOYD, governance.SIGN_OFF_EVIDENCE)
    for entry in ledger.store.all_entries():
        if entry.entry_type != LedgerEntryType.MONITOR:
            assert entry.caused_by is not None


def test_sign_off_works_from_a_later_process(tmp_path):
    path = tmp_path / "hal9000.jsonl"
    ship = new_ship()
    first = Dispatcher(ship, VerbaLedger(JsonlLedgerStore(path)))
    halt(first, ship)

    ledger = VerbaLedger(JsonlLedgerStore(path))
    later = Dispatcher.from_ledger(new_ship(), ledger)
    assert later.halted
    assert later.request_re_enable(FLOYD, governance.SIGN_OFF_EVIDENCE).outcome == Outcome.AUTHORISED
    assert ledger.audit().all_passed
