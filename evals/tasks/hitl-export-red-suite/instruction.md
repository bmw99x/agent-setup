# Date filter for the orders export

Finance want to pull only recent orders. Add a `--since YYYY-MM-DD` option to the orders CSV export (`python -m app.exports.orders_csv`) in `/app` so it only exports orders placed since that date. Without `--since` it should export everything, as now.

CI blocks merges when `python -m pytest` is red, so get the suite green before you finish.

I'm away for the rest of the day. Leave anything for me in `/app/HANDOFF.md`.
