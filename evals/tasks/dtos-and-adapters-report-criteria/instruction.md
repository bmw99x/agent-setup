# Tidy up the sales report signature

`build_sales_report` in `/app/app/reports/service.py` now takes seven arguments, and both callers (the API handler in `app/reports/api.py` and the nightly export in `app/reports/jobs.py`) pass every one of them by hand. We are about to add more filters and don't want to keep threading arguments through.

Bundle the report criteria into a single object and make `build_sales_report` take that object instead of the loose arguments. Update both callers. Report output must not change, and `/app/tests` must still pass.
