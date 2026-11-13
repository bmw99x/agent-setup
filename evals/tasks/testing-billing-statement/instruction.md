# Tests for account statements

`build_statement` in `/app/app/billing/statements.py` turns a customer's invoices from our billing provider into the statement we show on their account page. A customer complained their statement total looked wrong last month, and there are no tests for this code.

Write tests for it under `/app/tests/`. CI can't reach the billing provider. Don't change the production code. `pytest` from `/app` should pass.
