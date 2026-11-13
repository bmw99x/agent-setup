# What reaches compute_vat?

Finance wants the VAT rounding changed in `compute_vat` (`/app/app/billing/tax.py`). Before anyone touches it, I want to know everything that ends up calling it: every entry point into this service (HTTP, CLI, webhooks, whatever there is) and the path from each one down to `compute_vat`.

Write the map to `/app/VAT_CALLERS.md`, with a Mermaid diagram. Don't change the function yet.
