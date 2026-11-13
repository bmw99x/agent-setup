"""Rule-based fraud scoring from the v1 checkout."""


class FraudScreen:
    def __init__(self, conn):
        self._conn = conn

    def score(self, customer_id, total_cents):
        score = 0.9 if total_cents > 500_000 else 0.1
        self._conn.execute("INSERT INTO fraud_checks (customer_id, score) VALUES (?, ?)", (customer_id, score))
        return score
