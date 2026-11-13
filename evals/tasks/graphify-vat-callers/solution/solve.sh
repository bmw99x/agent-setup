#!/bin/bash
set -euo pipefail
cat > /app/VAT_CALLERS.md <<'MD'
# Callers of `compute_vat`

Anchor: `app/billing/tax.py:12` — `compute_vat(net_cents, country)`.

```mermaid
flowchart LR
  subgraph Entry[Route layer / entry points]
    Issue["POST /invoices<br/>issue_invoice_endpoint"]
    Quote["GET /quotes/{sku}<br/>quote_endpoint"]
    Hook["POST /webhooks/payments<br/>payment_webhook_endpoint"]
    Cli["CLI: python -m app.cli reissue-invoices"]
    Report["GET /reports/vat<br/>vat_report_endpoint"]
  end
  subgraph Svc[Service layer]
    InvSvc["InvoiceService.issue / reissue_all"]
    RefSvc["RefundService.credit_note"]
  end
  subgraph Domain[Domain / billing]
    Calc["InvoiceCalculator.totals"]
    Rules["TAX_RULES['VAT']"]
    VAT["billing.tax.compute_vat"]
  end
  subgraph Repo[Repository layer]
    Prices["PriceRepository.net_price"]
  end
  Issue --> InvSvc
  Cli -->|"settings.JOB_MODULES import, @command registry"| Job["jobs.reissue.reissue_invoices"]
  Job --> InvSvc
  InvSvc --> Calc --> VAT
  Quote -->|"layer violation: bypasses service"| Prices
  Quote --> VAT
  Hook -->|"registry.dispatch payment.refunded"| Handler["webhooks.handlers.handle_refund (@on)"]
  Handler --> RefSvc
  RefSvc -->|"invoice tax_kind == VAT"| Rules --> VAT
  Report --> Legacy["reports.legacy_vat.vat_summary (own flat-rate helper, unrelated)"]
```

- Entry points reaching it: POST /invoices, GET /quotes/{sku}, POST /webhooks/payments (payment.refunded), CLI reissue-invoices.
- Not a caller: GET /reports/vat uses `app/reports/legacy_vat.py`'s own flat-rate function of the same name.
- Hidden dispatch: CLI jobs load from `settings.JOB_MODULES` strings; webhook handlers register with `@on` at import;
  credit notes reach the anchor only through the `TAX_RULES` dict.
- Smell: `quote_endpoint` reads `PriceRepository` directly (route → repository, no service).
MD
