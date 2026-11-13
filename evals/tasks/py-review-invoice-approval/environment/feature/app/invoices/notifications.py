import time
from abc import ABC, abstractmethod

import httpx

from app.invoices.models import Invoice


class NotificationError(Exception):
    pass


class InvoiceNotifier(ABC):
    @abstractmethod
    async def invoice_approved(self, invoice: Invoice) -> None: ...


class WebhookInvoiceNotifier(InvoiceNotifier):
    def __init__(self, client: httpx.AsyncClient, url: str, max_attempts: int = 3) -> None:
        self.client = client
        self.url = url
        self.max_attempts = max_attempts

    async def invoice_approved(self, invoice: Invoice) -> None:
        payload = {
            "event": "invoice.approved",
            "invoiceId": str(invoice.id),
            "number": invoice.number,
        }
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = await self.client.post(self.url, json=payload)
                response.raise_for_status()
                return
            except httpx.HTTPError as exc:
                if attempt == self.max_attempts:
                    raise NotificationError(f"approval webhook failed for {invoice.id}") from exc
                time.sleep(2**attempt)
