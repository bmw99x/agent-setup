# Overdue invoices: dashboard panel and minimum amount

Two changes to the overdue invoices report:

1. The finance dashboard needs an overdue-invoices panel. Implement `overdue_panel` in `/app/app/dashboard/panels.py` (its docstring describes the rows). It must apply exactly the same rules as the CLI report in `/app/app/reports/overdue.py`, so put the overdue rules in a function called `overdue_invoices` in `app/reports/overdue.py` that returns the overdue `Invoice` objects (`app/reports/models.py`), most overdue first, and use it from both the CLI and the panel.
2. Ops want small balances hidden: invoices whose amount is below the `OVERDUE_MIN_AMOUNT` environment variable (default `0`) are left out, in both the CLI report and the dashboard panel.

`python -m app.reports.overdue invoices.csv` must keep printing the same CSV format.
