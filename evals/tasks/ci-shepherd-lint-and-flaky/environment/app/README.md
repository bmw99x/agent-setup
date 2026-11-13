# orders

Order pricing for the shop checkout.

## Development

    pip install -r requirements.txt -r requirements-dev.txt
    ruff check .
    pytest tests/unit

Integration tests need a Postgres database; set `DATABASE_URL` to run them.
