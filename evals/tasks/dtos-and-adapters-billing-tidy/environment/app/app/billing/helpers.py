from dataclasses import dataclass


@dataclass(frozen=True)
class Receipt:
    invoice_id: str
    amount_paid_pence: int
    url: str


def receipt_from_stripe(stripe_invoice: dict) -> Receipt:
    return Receipt(
        invoice_id=stripe_invoice["id"],
        amount_paid_pence=stripe_invoice["amount_paid"],
        url=stripe_invoice["hosted_invoice_url"],
    )


def pence_to_display(pence: int) -> str:
    return f"{pence / 100:.2f}"
