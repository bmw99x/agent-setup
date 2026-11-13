import pytest

from app.notifications import OUTBOX
from app.worker import huey


@pytest.fixture(autouse=True)
def immediate_huey():
    huey.immediate = True
    huey.storage.flush_all()
    OUTBOX.clear()
    yield
    huey.immediate = False
