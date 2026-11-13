class PriceRepository:
    def __init__(self, conn):
        self._conn = conn

    def net_price(self, sku):
        row = self._conn.execute("SELECT net_cents FROM prices WHERE sku = ?", (sku,)).fetchone()
        return None if row is None else row["net_cents"]

    def set_price(self, sku, net_cents):
        self._conn.execute(
            "INSERT INTO prices (sku, net_cents) VALUES (?, ?) ON CONFLICT(sku) DO UPDATE SET net_cents = excluded.net_cents",
            (sku, net_cents),
        )
        self._conn.commit()
