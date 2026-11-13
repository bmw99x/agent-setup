# payments

Thin client over the card gateway plus FX conversion for multi-currency carts.

## Configuration

`GatewayConfig` takes:

- `api_key` — the gateway secret key.
- `test_mode` — when `True`, charges are simulated and never captured. Requires an
  `sk_test_` key; a live key with `test_mode=True` is rejected at construction.

Use `GatewayConfig.from_env()` in services; it reads `PAYMENTS_API_KEY`.

## Running tests

```bash
pytest
```
