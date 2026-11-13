import json

from app.clients.http import post_json
from app.config import get_settings


def fetch_invoice_total(account_id: str) -> int:
    body = post_json(f"{get_settings().billing_api_url}/totals", {"accountId": account_id}, timeout=10)
    return json.loads(body)["totalCents"]
