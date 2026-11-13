# shipping

Delivery quotes for the checkout.

- `est_delivery(dispatched_on, service)` — the estimated delivery date shown at checkout.
- `latest_delivery(dispatched_on, service)` — the guaranteed latest date we promise in the
  confirmation email (`est_delivery` plus the service's buffer).
- `delivery_fee(weight_kg)` — the shipping charge in pence.

Ops can print a quote from the shell:

```bash
python -m app.cli 2026-03-06 standard 1.5
```
