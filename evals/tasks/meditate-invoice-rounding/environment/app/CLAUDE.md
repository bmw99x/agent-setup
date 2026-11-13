# billing-service

Invoice and ledger calculations for the storefront.

## Commands

- Tests: `pytest -q`
- Rebuild test fixtures: `scripts/regen_fixtures.sh`

## Learned rules

- Ledger amounts are stored in minor units in the database.
- Do not import from `billing.tools` in production code.
