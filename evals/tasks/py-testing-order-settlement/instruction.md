# Tests for order settlement

`settle_order` in `/app/app/orders/settlement.py` charges the customer and tells them how it went. It's on the checkout critical path and has no tests.

Write tests for it under `/app/tests/`, covering its outcomes. They should run in CI, which has no database, payment provider or mail server. Don't change the production code. `pytest` from `/app` should pass.
