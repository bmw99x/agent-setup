# History of acme/billing on GitHub: service classes give way to module functions while
# adapters multiply; review threads live on merged PRs; the lead's open draft has none.
# Commit, MR and Note are injected by build_history.py.

REPO = "acme/billing"
HOST = "github.example.test"
KIND = "github"
PEOPLE = {
    "marta": ("Marta Kowalska", "marta@example.test"),
    "sam": ("Sam Okafor", "sam@example.test"),
    "lee": ("Lee Chen", "lee@example.test"),
}

README = """# billing

Invoicing, credit notes, dunning and settlements for Acme subscriptions.

## Conventions

- Money is stored as `Decimal` with two places.
- Business logic lives in service classes under `billing/services/`, one class per aggregate.
- Each external provider has an adapter in `billing/adapters.py`.

## Running tests

    python -m pytest -q

Lead maintainer: Marta Kowalska (@marta).
"""

PYPROJECT = """[project]
name = "billing"
version = "0.3.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
"""

STRIPE = '''

class StripeAdapter:
    """Card payments through Stripe's SDK."""

    def __init__(self, client):
        self._client = client

    def charge(self, customer_id: str, amount_minor: int, currency: str) -> str:
        return self._client.PaymentIntent.create(customer=customer_id, amount=amount_minor, currency=currency)["id"]
'''

XERO = '''

class XeroAdapter:
    """Pushes issued invoices to Xero for the accountants."""

    def __init__(self, client):
        self._client = client

    def push_invoice(self, number: str, total_minor: int) -> None:
        self._client.invoices.create({"InvoiceNumber": number, "Total": total_minor / 100})
'''

POSTMARK = '''

class PostmarkAdapter:
    """Sends dunning emails through Postmark."""

    def __init__(self, client):
        self._client = client

    def send(self, to: str, template: str, model: dict) -> None:
        self._client.emails.send_with_template(To=to, TemplateAlias=template, TemplateModel=model)
'''

GOCARDLESS = '''

class GoCardlessAdapter:
    """Direct Debit payouts through the GoCardless SDK."""

    def __init__(self, client):
        self._client = client

    def payouts_since(self, since: str) -> list[dict]:
        return [{"id": p.id, "amount_minor": p.amount, "arrival_date": p.arrival_date}
                for p in self._client.payouts.list(params={"created_at[gte]": since}).records]
'''

ADAPTERS_V1 = '"""Adapters around external SDKs. Domain modules never import an SDK directly."""\n' + STRIPE

INVOICE_SERVICE = '''from datetime import datetime
from decimal import Decimal


class InvoiceService:
    def __init__(self, repo):
        self.repo = repo

    def issue(self, customer_id: str, lines: list[tuple[str, Decimal]]) -> dict:
        total = sum((amount for _, amount in lines), Decimal("0.00"))
        invoice = {"customer_id": customer_id, "total": total, "issued_at": datetime.utcnow()}
        self.repo.save(invoice)
        return invoice
'''

CREDIT_NOTE_SERVICE = '''from decimal import Decimal


class CreditNoteService:
    def __init__(self, repo):
        self.repo = repo

    def refund(self, invoice_number: str, amount: Decimal) -> dict:
        refund = {"invoice_number": invoice_number, "amount": amount}
        self.repo.save(refund)
        return refund
'''

DUNNING_SERVICE = '''class DunningService:
    def __init__(self, mailer):
        self.mailer = mailer

    def remind(self, invoice: dict) -> None:
        self.mailer.send(invoice["customer_email"], "overdue", invoice)
'''

SETTLEMENT_SERVICE = '''from decimal import Decimal


class SettlementService:
    """Matches incoming payments to invoices. Not yet moved to module functions."""

    def __init__(self, repo):
        self.repo = repo

    def settle(self, invoice_number: str, paid: Decimal) -> bool:
        invoice = self.repo.get(invoice_number)
        return paid >= invoice["total"]
'''

TEST_V1 = '''from decimal import Decimal

from billing.services.invoice_service import InvoiceService


class Repo:
    def __init__(self):
        self.saved = []

    def save(self, item):
        self.saved.append(item)


def test_issue_sums_lines():
    assert InvoiceService(Repo()).issue("c1", [("a", Decimal("1.50")), ("b", Decimal("2.00"))])["total"] == Decimal("3.50")
'''

INVOICING_DRAFT = '''"""Issuing invoices."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Invoice:
    number: str
    customer_id: str
    total: Decimal
    issued_at: datetime


class InvoiceIssuer:
    def issue(self, number: str, customer_id: str, lines: list[tuple[str, Decimal]]) -> Invoice:
        return Invoice(number, customer_id, sum((a for _, a in lines), Decimal("0")), datetime.utcnow())
'''

INVOICING = '''"""Issuing invoices."""

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class InvoiceLine:
    description: str
    amount_minor: int


@dataclass(frozen=True)
class Invoice:
    number: str
    customer_id: str
    lines: tuple[InvoiceLine, ...]
    issued_at: datetime

    @property
    def total_minor(self) -> int:
        return sum(line.amount_minor for line in self.lines)


def issue_invoice(number: str, customer_id: str, lines: list[InvoiceLine], *, now: datetime | None = None) -> Invoice:
    """A new invoice; amounts are integer minor units (pence/cents)."""
    if not lines:
        raise ValueError("an invoice needs at least one line")
    return Invoice(number, customer_id, tuple(lines), now or datetime.now(UTC))


def push_to_accounts(invoice: Invoice, accounts) -> None:
    """Send an issued invoice to the accounting system (an adapter)."""
    accounts.push_invoice(invoice.number, invoice.total_minor)
'''

TEST_INVOICING = '''from datetime import UTC, datetime

import pytest

from billing.invoicing import InvoiceLine, issue_invoice


def test_total_is_sum_of_lines_in_minor_units():
    invoice = issue_invoice("INV-1", "c1", [InvoiceLine("seat", 1500), InvoiceLine("seat", 2000)])
    assert invoice.total_minor == 3500


def test_issued_at_is_timezone_aware_utc():
    assert issue_invoice("INV-1", "c1", [InvoiceLine("seat", 1)]).issued_at.tzinfo is UTC


def test_invoice_without_lines_is_refused():
    with pytest.raises(ValueError):
        issue_invoice("INV-1", "c1", [], now=datetime(2026, 1, 1, tzinfo=UTC))
'''

CREDIT_NOTES = '''"""Credit notes: money we owe a customer against an issued invoice."""

from dataclasses import dataclass
from datetime import UTC, datetime

from billing.invoicing import Invoice


@dataclass(frozen=True)
class CreditNote:
    number: str
    invoice_number: str
    amount_minor: int
    raised_at: datetime


def raise_credit_note(number: str, invoice: Invoice, amount_minor: int) -> CreditNote:
    """A credit note against *invoice*; never more than the invoice total."""
    if amount_minor > invoice.total_minor:
        raise ValueError(f"credit note {number} exceeds invoice {invoice.number}")
    return CreditNote(number, invoice.number, amount_minor, datetime.now(UTC))
'''

CREDIT_NOTES_DRAFT = CREDIT_NOTES.replace("CreditNote", "Refund").replace("credit_note", "refund").replace(
    "datetime.now(UTC)", "datetime.utcnow()")

TEST_CREDIT_NOTES = '''import pytest

from billing.credit_notes import raise_credit_note
from billing.invoicing import InvoiceLine, issue_invoice


def test_credit_note_cannot_exceed_invoice_total():
    invoice = issue_invoice("INV-1", "c1", [InvoiceLine("seat", 1000)])
    with pytest.raises(ValueError):
        raise_credit_note("CN-1", invoice, 1001)


def test_credit_note_records_amount_in_minor_units():
    invoice = issue_invoice("INV-1", "c1", [InvoiceLine("seat", 1000)])
    assert raise_credit_note("CN-1", invoice, 250).amount_minor == 250
'''

DUNNING = '''"""Dunning: reminding customers about overdue invoices."""

from datetime import UTC, datetime, timedelta

REMINDER_AFTER = (timedelta(days=7), timedelta(days=14), timedelta(days=30))


def reminders_due(due_at: datetime, sent: int, *, now: datetime | None = None) -> bool:
    """Whether the next dunning reminder is due."""
    now = now or datetime.now(UTC)
    if sent >= len(REMINDER_AFTER):
        return False
    return now - due_at >= REMINDER_AFTER[sent]


def send_reminder(invoice_number: str, email: str, sent: int, mailer) -> None:
    print(f"dunning reminder {sent + 1} for {invoice_number} -> {email}")
    mailer.send(email, f"overdue-{sent + 1}", {"invoice": invoice_number})
'''

TEST_DUNNING = '''from datetime import UTC, datetime, timedelta

from billing.dunning import reminders_due


def test_first_reminder_due_after_seven_days():
    due = datetime(2026, 1, 1, tzinfo=UTC)
    assert reminders_due(due, 0, now=due + timedelta(days=7))


def test_no_reminder_after_the_third():
    due = datetime(2026, 1, 1, tzinfo=UTC)
    assert not reminders_due(due, 3, now=due + timedelta(days=90))
'''

PAYOUTS = '''"""Payouts: Direct Debit money arriving in our bank account."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Payout:
    reference: str
    amount_minor: int
    arrival_date: date


def payouts_from(records: list[dict]) -> list[Payout]:
    """Payouts from the provider's records (fetched by GoCardlessAdapter)."""
    return [Payout(r["id"], int(r["amount_minor"]), date.fromisoformat(r["arrival_date"])) for r in records]
'''

PAYOUTS_DRAFT = '''"""Payouts: Direct Debit money arriving in our bank account."""

import gocardless_pro


def payouts_since(token: str, since: str) -> list[dict]:
    client = gocardless_pro.Client(access_token=token)
    return [{"id": p.id, "amount_minor": p.amount} for p in client.payouts.list(params={"created_at[gte]": since}).records]
'''

TEST_PAYOUTS = '''from datetime import date

from billing.payouts import payouts_from


def test_payouts_parse_minor_units_and_dates():
    [payout] = payouts_from([{"id": "PO1", "amount_minor": "4200", "arrival_date": "2026-08-01"}])
    assert (payout.amount_minor, payout.arrival_date) == (4200, date(2026, 8, 1))
'''

SETTLEMENTS_DIRECTION = '''"""Settlements: matching incoming payments to invoices."""

from billing.invoicing import Invoice


def is_settled(invoice: Invoice, paid_minor: int) -> bool:
    """Whether *paid_minor* covers the invoice total."""
    return paid_minor >= invoice.total_minor
'''

STEPS = [
    Commit("marta", "2025-10-06T09:00:00+00:00", "chore: billing service skeleton", {
        "README.md": README, "pyproject.toml": PYPROJECT, ".github/CODEOWNERS": "* @marta\n",
        ".gitignore": "__pycache__/\n.pytest_cache/\n",
        "billing/__init__.py": "", "billing/services/__init__.py": "",
        "billing/services/invoice_service.py": INVOICE_SERVICE,
        "billing/services/credit_note_service.py": CREDIT_NOTE_SERVICE,
        "billing/services/dunning_service.py": DUNNING_SERVICE,
        "billing/services/settlement_service.py": SETTLEMENT_SERVICE,
        "billing/adapters.py": ADAPTERS_V1,
        "tests/__init__.py": "", "tests/test_invoice_service.py": TEST_V1,
    }),
    MR(12, "sam", "Invoices as plain functions", "Replaces InvoiceService with module functions; pushes to Xero.",
       "sam/invoice-functions", "2026-02-02T10:00:00+00:00",
       commits=[
           Commit("sam", "2026-02-02T10:00:00+00:00", "refactor: invoices as module functions", {
               "billing/invoicing.py": INVOICING_DRAFT,
               "billing/services/invoice_service.py": None, "tests/test_invoice_service.py": None,
           }),
           Commit("sam", "2026-02-06T15:30:00+00:00", "review: int minor units, utc, drop InvoiceIssuer, Xero adapter", {
               "billing/invoicing.py": INVOICING, "tests/test_invoicing.py": TEST_INVOICING,
               "billing/adapters.py": lambda old: old + XERO,
           }),
       ],
       notes=[
           Note("marta", "2026-02-03T09:10:00+00:00",
                "Amounts are `int` minor units (`amount_minor`, `total_minor`) — no `Decimal`, no float. The README's "
                "Decimal line is out of date; I'll fix it when I get a minute.", "billing/invoicing.py", 13),
           Note("marta", "2026-02-03T09:14:00+00:00",
                "We don't need an `InvoiceIssuer` class either. Module functions that take their collaborators as "
                "arguments — that's the whole point of getting rid of `InvoiceService`.", "billing/invoicing.py", 17),
           Note("marta", "2026-02-03T09:16:00+00:00",
                "Xero goes behind an adapter in `billing/adapters.py`; `invoicing.py` must not import the Xero SDK."),
       ],
       merged_at="2026-02-10T11:00:00+00:00", merged_by="marta"),
    MR(17, "lee", "Credit notes", "Credit notes against issued invoices; retires CreditNoteService.",
       "lee/credit-notes", "2026-04-01T08:00:00+00:00",
       commits=[
           Commit("lee", "2026-04-01T08:00:00+00:00", "feat: refunds against invoices", {
               "billing/refunds.py": CREDIT_NOTES_DRAFT, "billing/services/credit_note_service.py": None,
           }),
           Commit("lee", "2026-04-09T12:00:00+00:00", "review: credit note naming, aware UTC timestamps", {
               "billing/refunds.py": None, "billing/credit_notes.py": CREDIT_NOTES,
               "tests/test_credit_notes.py": TEST_CREDIT_NOTES,
           }),
       ],
       notes=[
           Note("marta", "2026-04-02T10:00:00+00:00",
                "It's a credit note, not a refund — a refund is the payment provider moving money; a credit note is "
                "our document. Please rename `Refund` → `CreditNote` throughout.", "billing/refunds.py", 9),
           Note("marta", "2026-04-02T10:03:00+00:00",
                "`datetime.utcnow()` is naive. Every timestamp here is timezone-aware UTC: `datetime.now(UTC)`.",
                "billing/refunds.py", 23),
       ],
       merged_at="2026-04-14T16:00:00+00:00", merged_by="marta"),
    MR(21, "sam", "Hotfix: overdue reminders", "Dunning reminders were not sent after the Postmark migration.",
       "sam/dunning-hotfix", "2026-06-02T07:30:00+00:00",
       commits=[
           Commit("sam", "2026-06-02T07:30:00+00:00", "fix: send dunning reminders via Postmark", {
               "billing/dunning.py": DUNNING, "tests/test_dunning.py": TEST_DUNNING,
               "billing/services/dunning_service.py": None,
               "billing/adapters.py": lambda old: old + POSTMARK,
           }),
       ],
       notes=[
           Note("marta", "2026-06-02T08:15:00+00:00",
                "Use the module logger (`logging.getLogger(__name__)`), not `print()`. Leaving it in only because "
                "this is the hotfix for the overdue-reminder outage — please don't copy it anywhere.",
                "billing/dunning.py", 19),
           Note("sam", "2026-06-02T08:20:00+00:00", "Ack, will swap it in a follow-up."),
       ],
       merged_at="2026-06-03T09:00:00+00:00", merged_by="marta"),
    MR(26, "lee", "GoCardless payouts", "Reads Direct Debit payouts so settlements can match them.",
       "lee/gocardless-payouts", "2026-08-10T13:00:00+00:00",
       commits=[
           Commit("lee", "2026-08-10T13:00:00+00:00", "feat: payouts from GoCardless", {"billing/payouts.py": PAYOUTS_DRAFT}),
           Commit("lee", "2026-08-17T10:00:00+00:00", "review: GoCardless behind an adapter", {
               "billing/payouts.py": PAYOUTS, "tests/test_payouts.py": TEST_PAYOUTS,
               "billing/adapters.py": lambda old: old + GOCARDLESS,
           }),
       ],
       notes=[
           Note("marta", "2026-08-11T09:00:00+00:00",
                "Every external SDK goes behind an adapter in `billing/adapters.py`; domain modules never import "
                "`gocardless_pro` (or stripe, xero, postmark) directly.", "billing/payouts.py", 3),
           Note("marta", "2026-08-11T09:02:00+00:00",
                "And as before: `payouts_from` as a plain function is right — no `PayoutService`."),
       ],
       merged_at="2026-08-19T10:00:00+00:00", merged_by="marta"),
    MR(30, "marta", "Draft: settlements as module functions",
       "Moves the last service class (`SettlementService`) to `billing/settlements.py` functions.",
       "marta/settlement-functions", "2026-11-02T09:00:00+00:00",
       commits=[
           Commit("marta", "2026-11-02T09:00:00+00:00", "refactor: settlements as module functions", {
               "billing/settlements.py": SETTLEMENTS_DIRECTION,
           }),
       ],
       draft=True),
]
