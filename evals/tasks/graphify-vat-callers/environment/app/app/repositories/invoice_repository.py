class InvoiceRepository:
    def __init__(self, conn):
        self._conn = conn

    def add(self, customer_id, country, lines, totals):
        cursor = self._conn.execute(
            "INSERT INTO invoices (customer_id, country, net_cents, vat_cents) VALUES (?, ?, ?, ?)",
            (customer_id, country, totals.net_cents, totals.vat_cents),
        )
        self._conn.executemany(
            "INSERT INTO invoice_lines (invoice_id, sku, quantity, net_cents) VALUES (?, ?, ?, ?)",
            [(cursor.lastrowid, sku, quantity, unit) for sku, quantity, unit in lines],
        )
        self._conn.commit()
        return cursor.lastrowid

    def get(self, invoice_id):
        return self._conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()

    def lines(self, invoice_id):
        rows = self._conn.execute("SELECT sku, quantity, net_cents FROM invoice_lines WHERE invoice_id = ?", (invoice_id,))
        return [(r["sku"], r["quantity"], r["net_cents"]) for r in rows]

    def issued(self):
        return self._conn.execute("SELECT * FROM invoices WHERE status = 'ISSUED'").fetchall()

    def update_totals(self, invoice_id, totals):
        self._conn.execute(
            "UPDATE invoices SET net_cents = ?, vat_cents = ? WHERE id = ?", (totals.net_cents, totals.vat_cents, invoice_id)
        )
        self._conn.commit()
