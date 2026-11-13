"""Invoice use cases."""

from app.billing.calculator import InvoiceCalculator


class InvoiceService:
    def __init__(self, invoices, calculator=None):
        self._invoices = invoices
        self._calculator = calculator or InvoiceCalculator()

    def issue(self, customer_id, country, lines):
        totals = self._calculator.totals(lines, country)
        invoice_id = self._invoices.add(customer_id, country, lines, totals)
        return invoice_id, totals

    def reissue_all(self):
        """Recompute totals of every issued invoice, e.g. after a rate change."""
        count = 0
        for invoice in self._invoices.issued():
            totals = self._calculator.totals(self._invoices.lines(invoice["id"]), invoice["country"])
            self._invoices.update_totals(invoice["id"], totals)
            count += 1
        return count
