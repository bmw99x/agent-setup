# finance

Finance services monorepo. Each directory under `services/` is its own uv project with its own
`pyproject.toml` and `uv.lock`, deployed independently.

| Service | What it does |
|---|---|
| `services/billing` | Issues invoices, converts foreign-currency charges, posts to the general ledger |
| `services/reports` | Monthly revenue summaries and CSV exports for finance |
| `services/notifications` | Sends invoice and dunning emails |
