"""Card acquirer client."""

import uuid


class Gateway:
    def charge(self, customer_id, amount_cents):
        if amount_cents <= 0:
            raise ValueError("amount must be positive")
        return f"card_{uuid.uuid4().hex[:12]}"
