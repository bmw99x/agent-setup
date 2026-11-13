"""Refunds become credit notes against the original invoice."""

from app.billing.tax_rules import TAX_RULES


class RefundService:
    def __init__(self, invoices, credit_notes):
        self._invoices = invoices
        self._credit_notes = credit_notes

    def credit_note(self, invoice_id, refunded_net_cents):
        invoice = self._invoices.get(invoice_id)
        if invoice is None:
            raise LookupError(f"invoice {invoice_id} not found")
        vat_cents = TAX_RULES[invoice["tax_kind"]](refunded_net_cents, invoice["country"])
        return self._credit_notes.add(invoice_id, refunded_net_cents, vat_cents)
