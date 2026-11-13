# Loyalty job: one connection, and a birthday bonus

The monthly loyalty job (`LOYALTY_DB=... python -m app.loyalty.job 2026-10`, code in `/app/app/loyalty/`) opens a new SQLite connection for every customer. With 200k customers the run takes hours. Make a run use a single connection.

While you're in there, add the birthday bonus marketing asked for: in a customer's birthday month (`customers.birth_month`), the points earned from orders are doubled. The 500-point streak bonus is then checked against the doubled figure.

Keep `run_monthly_award(month)` and the command line working; the scheduler calls both. The schema is in `app/loyalty/schema.sql` and must not change.
