import json
import urllib.request
from dataclasses import dataclass


@dataclass
class BankClient:
    """The partner bank's transfer API."""

    base_url: str
    api_key: str

    def send_transfer(self, account_id: str, amount_pence: int, reference: str) -> str:
        body = json.dumps({"account": account_id, "amount": amount_pence, "reference": reference}).encode()
        request = urllib.request.Request(
            f"{self.base_url}/transfers", data=body, headers={"Authorization": f"Bearer {self.api_key}"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)["transfer_id"]
