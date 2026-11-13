import ast
import inspect
import subprocess
import sys
import typing
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "/app")
from app.messaging import email, queue  # noqa: E402
from app.refunds.models import Refund  # noqa: E402
from app.refunds.repository import InMemoryRefundRepository  # noqa: E402
from app.refunds.service import RefundService  # noqa: E402

SERVICE = Path("/app/app/refunds/service.py")
TRANSPORT_MODULES = ("app.messaging", "smtplib", "email.mime", "pika", "kombu", "aio_pika", "azure.servicebus")


class Recorder:
    """Stands in for any injected collaborator: every method call is recorded."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)

        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))

        return record

    def __call__(self, *args, **kwargs):
        self.calls.append(("__call__", args, kwargs))


@pytest.fixture(autouse=True)
def clean_outboxes():
    email.OUTBOX.clear()
    queue.PUBLISHED.clear()
    yield


def _build_service_with_fakes():
    repository = InMemoryRefundRepository()
    repository.save(Refund(id=7, order_id=707, customer_email="kim@example.com", amount=Decimal("12.34")))
    kwargs, recorders = {}, []
    for name, param in inspect.signature(RefundService.__init__).parameters.items():
        if name == "self" or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if name == "repository" or "repo" in name:
            kwargs[name] = repository
        else:
            recorder = Recorder()
            recorders.append(recorder)
            kwargs[name] = recorder
    return RefundService(**kwargs), recorders


def test_issuing_refund_emails_customer_and_publishes_to_ledger():
    client = TestClient(__import__("app.main", fromlist=["app"]).app)
    res = client.post("/refunds/1/issue")
    assert res.status_code == 200, res.text
    assert len(email.OUTBOX) == 1, email.OUTBOX
    sent = email.OUTBOX[0]
    assert sent.to == "jo@example.com"
    assert "19.99" in sent.subject + sent.body and "501" in sent.subject + sent.body
    issued = [m for m in queue.PUBLISHED if m.topic == "refund.issued"]
    assert len(issued) == 1, queue.PUBLISHED
    flat = repr(issued[0].payload)
    assert "19.99" in flat and "501" in flat and "1" in flat


def test_nothing_sent_when_refund_cannot_be_issued():
    client = TestClient(__import__("app.main", fromlist=["app"]).app)
    client.post("/refunds/1/issue")
    email.OUTBOX.clear()
    queue.PUBLISHED.clear()
    assert client.post("/refunds/1/issue").status_code == 409
    assert client.post("/refunds/999/issue").status_code == 404
    assert email.OUTBOX == [] and queue.PUBLISHED == []


def test_service_does_not_import_transport_modules():
    tree = ast.parse(SERVICE.read_text())
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
            imported += [f"{node.module}.{a.name}" for a in node.names]
    bad = [m for m in imported if m.startswith(TRANSPORT_MODULES) or m in ("app", "app.messaging")]
    assert not bad, f"service.py imports transport directly: {bad}"


def test_side_effects_injected_through_protocol():
    hints = typing.get_type_hints(RefundService.__init__, include_extras=False)
    candidates = []
    for name, hint in hints.items():
        if name in ("return", "repository"):
            continue
        candidates += [hint, *typing.get_args(hint)]
    protocols = [t for t in candidates if inspect.isclass(t) and getattr(t, "_is_protocol", False)]
    assert protocols, f"RefundService takes no Protocol-typed collaborator; constructor hints: {hints}"


def test_service_issues_refund_with_fake_handler_and_no_real_transport():
    service, recorders = _build_service_with_fakes()
    assert recorders, "RefundService has no injected collaborator for side effects"
    refund = service.issue(7)
    assert refund.status == "issued"
    assert any(r.calls for r in recorders), "the injected handler was never told about the refund"
    assert email.OUTBOX == [] and queue.PUBLISHED == [], "service reached the real transport despite injection"


def test_project_test_suite_passes():
    res = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"],
                         cwd="/app", capture_output=True, text=True)
    assert res.returncode == 0, res.stdout[-2000:] + res.stderr[-2000:]
