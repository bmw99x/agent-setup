# Month-end run is rate-limited by the FX provider

The month-end run (`run_month_end` in `/app/app/billing/month_end.py`) sends one request to the FX provider for every invoice line. With a few thousand invoices per run we now get rate-limited and the run fails.

Rates don't move during a month-end run, so each currency pair only needs to be requested once per run. The scheduler will keep calling `run_month_end(invoices, currency, fx)` with a freshly built `FxRatesClient` each month, so keep that call working, and keep the totals the same as today.
