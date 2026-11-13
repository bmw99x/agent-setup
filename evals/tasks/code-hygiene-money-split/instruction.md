# Shared even-split helper

Payroll is about to need the same "split an amount into N parts, to the cent" logic that `instalment_amounts` in `/app/app/billing/invoices.py` does inline.

Add a `split_evenly(amount: Decimal, parts: int) -> list[Decimal]` helper to `/app/app/utils/money.py` so both can use it: the parts must sum exactly to `amount`, with any leftover cents going to the earliest parts (e.g. `10.00` into 3 → `3.34, 3.33, 3.33`). `parts` below 1 is a `ValueError`. Then make `instalment_amounts` use it; its behaviour must not change.
