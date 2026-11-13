class CreditNoteRepository:
    def __init__(self, conn):
        self._conn = conn

    def add(self, invoice_id, net_cents, vat_cents):
        cursor = self._conn.execute(
            "INSERT INTO credit_notes (invoice_id, net_cents, vat_cents) VALUES (?, ?, ?)", (invoice_id, net_cents, vat_cents)
        )
        self._conn.commit()
        return cursor.lastrowid
