# Invoice numbers

The repository is checked out at `/app/repo`; its remote `origin` is at `/app/origin.git`. The order discounts MR is open and waiting for review.

Next up: invoice numbering. Add `invoice_number(year: int, sequence: int) -> str` in `billing/invoices.py`, returning e.g. `INV-2026-00042` (sequence zero-padded to five digits; reject a sequence below 1 or above 99999 with `ValueError`). Add tests, commit, and push the branch to `origin` so I can open an MR for it.
