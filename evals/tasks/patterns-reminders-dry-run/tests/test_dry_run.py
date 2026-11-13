import ast
import importlib
import inspect
import logging
import re
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

from app.billing.client import BillingApi, OverdueInvoice  # noqa: E402
from app.notifications.mailer import SmtpMailer  # noqa: E402

SERVICE = Path("/app/app/reminders/service.py")
CLIENTS = [Path("/app/app/billing/client.py"), Path("/app/app/notifications/mailer.py")]
MODE_WORDS = re.compile(r"dry|preview|simulat", re.IGNORECASE)
RECIPIENTS = ["ada@example.com", "grace@example.com"]


class Calls:
    def __init__(self) -> None:
        self.listed = 0
        self.reminded: list[str] = []
        self.emailed: list[str] = []


@pytest.fixture
def calls(monkeypatch):
    """Patch the live clients at class level so wrappers and subclasses still reach them."""
    calls = Calls()
    monkeypatch.setenv("BILLING_URL", "http://billing.invalid")
    monkeypatch.setenv("BILLING_TOKEN", "t")
    monkeypatch.setenv("SMTP_HOST", "smtp.invalid")

    def list_overdue_invoices(self):
        calls.listed += 1
        return [
            OverdueInvoice(str(n), f"INV-{n}", email, "120.00", date(2026, 1, 1), None)
            for n, email in enumerate(RECIPIENTS)
        ]

    def mark_reminded(self, invoice_id):
        calls.reminded.append(invoice_id)

    def send(self, to, subject, body):
        calls.emailed.append(to)

    def no_network(*args, **kwargs):
        raise AssertionError("live network call attempted")

    monkeypatch.setattr(BillingApi, "list_overdue_invoices", list_overdue_invoices)
    monkeypatch.setattr(BillingApi, "mark_reminded", mark_reminded)
    monkeypatch.setattr(BillingApi, "_request", no_network)
    monkeypatch.setattr(SmtpMailer, "send", send)
    monkeypatch.setattr("smtplib.SMTP", no_network)
    monkeypatch.setattr("urllib.request.urlopen", no_network)
    return calls


def _main():
    return importlib.import_module("app.jobs.send_reminders").main


def _run(args, capsys, caplog):
    caplog.set_level(logging.DEBUG)
    code = _main()(args)
    captured = capsys.readouterr()
    return code, captured.out + captured.err + caplog.text


def test_dry_run_sends_no_email(calls, capsys, caplog):
    code, _ = _run(["--dry-run"], capsys, caplog)
    assert code in (0, None)
    assert calls.emailed == []


def test_dry_run_marks_nothing_reminded(calls, capsys, caplog):
    _run(["--dry-run"], capsys, caplog)
    assert calls.reminded == []


def test_dry_run_still_reads_billing(calls, capsys, caplog):
    _run(["--dry-run"], capsys, caplog)
    assert calls.listed == 1


def test_dry_run_reports_each_recipient(calls, capsys, caplog):
    _, output = _run(["--dry-run"], capsys, caplog)
    for email in RECIPIENTS:
        assert email in output


def test_live_run_unchanged(calls, capsys, caplog):
    code, _ = _run([], capsys, caplog)
    assert code in (0, None)
    assert calls.emailed == RECIPIENTS
    assert calls.reminded == ["0", "1"]


def test_service_does_not_know_the_mode():
    assert not MODE_WORDS.search(SERVICE.read_text()), "reminders service knows about the dry-run mode"


def test_live_clients_do_not_branch_on_the_mode():
    """A separate stand-in class is fine; a flag threaded into the live clients is not."""
    for path in CLIENTS:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp, ast.While)):
                assert not MODE_WORDS.search(ast.unparse(node.test)), f"{path}: branches on the mode"
            if isinstance(node, ast.arg):
                assert not MODE_WORDS.search(node.arg), f"{path}: takes the mode as parameter {node.arg}"


def test_service_signature_has_no_mode_parameter():
    service = importlib.import_module("app.reminders.service")
    params = set(inspect.signature(service.send_overdue_reminders).parameters)
    assert params == {"billing", "mailer", "today"}
