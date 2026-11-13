import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class OverdueInvoice:
    id: str
    number: str
    customer_email: str
    amount_due: str
    due_on: date
    reminded_on: date | None


class BillingApi:
    """Client for the billing service's HTTP API."""

    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token

    @classmethod
    def from_env(cls) -> "BillingApi":
        return cls(os.environ["BILLING_URL"], os.environ["BILLING_TOKEN"])

    def _request(self, method: str, path: str) -> dict:
        request = urllib.request.Request(
            f"{self._base_url}{path}",
            method=method,
            headers={"Authorization": f"Bearer {self._token}"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read() or b"{}")

    def list_overdue_invoices(self) -> list[OverdueInvoice]:
        payload = self._request("GET", "/invoices?status=overdue")
        return [
            OverdueInvoice(
                id=item["id"],
                number=item["number"],
                customer_email=item["customer_email"],
                amount_due=item["amount_due"],
                due_on=date.fromisoformat(item["due_on"]),
                reminded_on=date.fromisoformat(item["reminded_on"]) if item["reminded_on"] else None,
            )
            for item in payload["items"]
        ]

    def mark_reminded(self, invoice_id: str) -> None:
        self._request("POST", f"/invoices/{invoice_id}/reminded")
