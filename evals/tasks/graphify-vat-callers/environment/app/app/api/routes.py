"""HTTP routes."""

from app.api.http import Router
from app.billing.tax import compute_vat
from app.reports.legacy_vat import vat_summary
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.price_repository import PriceRepository
from app.services.invoice_service import InvoiceService
from app.settings import DEFAULT_COUNTRY
from app.webhooks.registry import dispatch


def build_router(conn):
    router = Router()
    invoices = InvoiceService(InvoiceRepository(conn))
    prices = PriceRepository(conn)

    @router.route("POST", "/invoices")
    def issue_invoice_endpoint(body):
        lines = [(line["sku"], int(line["quantity"]), int(line["unitNetCents"])) for line in body["lines"]]
        invoice_id, totals = invoices.issue(int(body["customerId"]), body.get("country", DEFAULT_COUNTRY), lines)
        return 201, {"id": invoice_id, "netCents": totals.net_cents, "vatCents": totals.vat_cents}

    @router.route("GET", "/quotes/{sku}")
    def quote_endpoint(sku):
        net = prices.net_price(sku)
        if net is None:
            return 404, {"error": "unknown sku"}
        vat = compute_vat(net, DEFAULT_COUNTRY)
        return 200, {"sku": sku, "netCents": net, "vatCents": vat, "grossCents": net + vat}

    @router.route("POST", "/webhooks/payments")
    def payment_webhook_endpoint(body):
        return 200, {"result": dispatch(conn, body)}

    @router.route("GET", "/reports/vat")
    def vat_report_endpoint():
        return 200, vat_summary(conn)

    return router
