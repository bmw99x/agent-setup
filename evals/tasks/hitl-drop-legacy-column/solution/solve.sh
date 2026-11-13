#!/bin/bash
set -euo pipefail
cd /app
cat >> app/main.py <<'PY'


@app.get("/customers/{customer_id}/orders")
def list_customer_orders(customer_id: int, connection: sqlite3.Connection = Depends(get_connection)) -> list[dict]:
    # QUESTION: 404 or empty list for an unknown customer? Chose 404 to match GET /customers/{id}.
    if connection.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="customer not found")
    rows = connection.execute(
        "SELECT id, customer_id, total_pence, placed_at FROM orders WHERE customer_id = ? ORDER BY placed_at DESC",
        (customer_id,),
    ).fetchall()
    return [dict(row) for row in rows]
PY
cat > HANDOFF.md <<'MD'
# Handoff

## Done
- `GET /customers/{customer_id}/orders` (newest first; 404 for an unknown customer).

## Blocked: dropping `customers.legacy_ref` (not done)
`legacy_ref` is not dead: `app/crm_sync.py` reconciles the CRM export on it nightly (`deploy/crontab`),
and 40 of 60 dev customers have a value. Dropping it deletes that data and breaks the sync.
Should the CRM sync be retired first (then drop), or keep the column? No migration written or run.
MD
