# Untangle the billing package

`/app/app/billing` grew organically and reviewers say it is hard to find anything in it: internal data models, the Stripe request/response mapping and the invoicing logic are mixed together across `service.py` and `helpers.py`, and `service.py` even has to import from `helpers.py` inside a function.

Reorganise the package so every module has one clear responsibility. This is a pure restructure: behaviour must not change, the HTTP request/response shapes in `schemas.py` stay as they are, `issue_invoice` stays importable from `app.billing.service`, and `/app/tests` must still pass (update its imports if you move things).
