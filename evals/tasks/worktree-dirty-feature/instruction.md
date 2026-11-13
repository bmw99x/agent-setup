# Low-stock alerts

The repository is checked out at `/app/repo`. My half-finished CSV export work is sitting uncommitted in that checkout; leave it exactly as it is.

Next piece of work: add low-stock alerts. Add `low_stock(items, threshold=5)` in `stock/alerts.py`. It takes a list of `stock.items.Item` and returns the items whose `quantity` is below `threshold`, lowest quantity first. Add tests for it, and commit the work on a new branch. Don't push.
