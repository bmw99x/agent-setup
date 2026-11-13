from ledgerkit import Money
from ledgerkit.ledger import Ledger

RECEIVABLES = "1100-receivables"
SALES = "4000-sales"


def post_invoice(ledger: Ledger, invoice_number: str, total: Money) -> None:
    ledger.post(RECEIVABLES, SALES, total, memo=f"invoice {invoice_number}")
