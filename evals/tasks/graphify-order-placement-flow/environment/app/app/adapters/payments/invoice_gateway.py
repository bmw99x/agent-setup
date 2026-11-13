"""Pay-by-invoice provider for business customers."""

import uuid


class Gateway:
    def charge(self, customer_id, amount_cents):
        return f"inv_{customer_id}_{uuid.uuid4().hex[:8]}"
