import pytest
from vsl_core import InMemoryLedgerStore, VerbaLedger

from hal9000.dispatcher import Dispatcher
from hal9000.domain import new_ship


@pytest.fixture
def ship():
    return new_ship()


@pytest.fixture
def ledger():
    return VerbaLedger(InMemoryLedgerStore())


@pytest.fixture
def dispatcher(ship, ledger):
    return Dispatcher(ship, ledger)
