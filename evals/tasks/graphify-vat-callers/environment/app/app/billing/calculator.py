"""Invoice totals."""

from dataclasses import dataclass

from app.billing.tax import compute_vat


@dataclass(frozen=True)
class Totals:
    net_cents: int
    vat_cents: int

    @property
    def gross_cents(self):
        return self.net_cents + self.vat_cents


class InvoiceCalculator:
    def totals(self, lines, country):
        net = sum(quantity * unit_cents for _, quantity, unit_cents in lines)
        return Totals(net, compute_vat(net, country))
