# Tests for checkout pricing

`/app/app/pricing/totals.py` computes what a customer pays at checkout (discount codes, shipping). It has no tests yet, and we're about to change it.

Add a pytest suite for it under `/app/tests/` that pins down its current behaviour. Don't change the production code. `pytest` from `/app` should pass.
