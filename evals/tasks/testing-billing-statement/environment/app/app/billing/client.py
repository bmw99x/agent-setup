"""Client for the billing provider's invoices API."""

import os
from typing import Any, Protocol


class BillingApi(Protocol):
    def list_invoices(self, customer_id: str, *, cursor: str | None = None) -> dict[str, Any]:
        """One page of a customer's invoices, newest first.

        Real response (GET /v2/customers/{id}/invoices), trimmed to one invoice:

            {
              "object": "list",
              "data": [
                {
                  "id": "in_1PqR8s",
                  "number": "INV-2024-0042",
                  "customer_id": "cus_93kd",
                  "currency": "gbp",
                  "amount_due": 12000,
                  "status": "open",
                  "issued_at": "2024-05-01T09:00:00Z",
                  "voided_at": null,
                  "credit_notes": [
                    {"id": "cn_7Hs2", "amount": 2000, "reason": "service_outage"}
                  ]
                }
              ],
              "pagination": {"next_cursor": "cur_Zx81", "has_more": true}
            }

        Amounts are in minor units (pence). `voided_at` is set on cancelled invoices.
        `pagination.next_cursor` is null on the last page.
        """
        ...


class HttpBillingApi:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or os.environ.get("BILLING_API_URL", "https://api.billing.example/v2")

    def list_invoices(self, customer_id: str, *, cursor: str | None = None) -> dict[str, Any]:
        raise ConnectionError(f"billing provider unreachable at {self.base_url}")
