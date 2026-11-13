# Extract the retry loop into a decorator

`EcbRateClient` in `/app/app/rates/ecb_client.py` has the same retry loop copy-pasted into both methods, and two more clients are about to copy it again.

Add a reusable async retry decorator `retry` in `/app/app/retry.py`, used as `@retry(attempts=3)` on an `async def` function or method: it re-runs the call when it raises `app.errors.TransientError`, up to `attempts` calls in total, then re-raises the last error. Other exceptions propagate immediately. Apply it to both `EcbRateClient` methods and remove the copy-pasted loops.

The decorator will go on methods of many clients, including ones passed around as `RateSource`. Decorated functions must keep being type-checked exactly as before: callers still get their argument and return types checked.

`mypy` (configured in `pyproject.toml`, strict) and `pytest` must pass. Don't silence mypy with `# type: ignore`.
