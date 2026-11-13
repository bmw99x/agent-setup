# catalog-sync

Pulls products, categories and price feeds from the supplier API and pushes our stock levels back.

```bash
uv sync
python -m app.jobs.retrying
```
