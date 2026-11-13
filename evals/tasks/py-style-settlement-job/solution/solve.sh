#!/bin/bash
set -euo pipefail
cat > /app/app/settlements/exceptions.py <<'PY'
class SettlementError(Exception):
    """Base error for settlement processing."""


class MalformedSettlementFileError(SettlementError):
    def __init__(self, blob_name: str, reason: str) -> None:
        super().__init__(f"Malformed settlement file {blob_name}: {reason}")
        self.blob_name = blob_name
PY
cat > /app/app/settlements/job.py <<'PY'
import csv
import io
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import NewType

from azure.identity import AzureCliCredential, ChainedTokenCredential, ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient, ContainerClient

from app.observability.logging import get_logger
from app.settings import load_settings
from app.settlements.exceptions import MalformedSettlementFileError

SETTLEMENTS_CONTAINER = "settlements"
SETTLEMENT_FILE_SUFFIX = ".csv"
REQUIRED_COLUMNS = {"merchant_id", "amount"}

logger = get_logger(__name__)

MerchantId = NewType("MerchantId", str)


def parse_settlement_file(blob_name: str, content: str) -> dict[MerchantId, Decimal]:
    reader = csv.DictReader(io.StringIO(content))
    missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing_columns:
        raise MalformedSettlementFileError(blob_name, f"missing columns {sorted(missing_columns)}")
    totals_in_file: dict[MerchantId, Decimal] = defaultdict(Decimal)
    for row in reader:
        try:
            amount = Decimal(row["amount"])
        except InvalidOperation as error:
            raise MalformedSettlementFileError(blob_name, f"bad amount {row['amount']!r}") from error
        totals_in_file[MerchantId(row["merchant_id"])] += amount
    return totals_in_file


def total_settlements(container_client: ContainerClient) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for blob in container_client.list_blobs():
        if not blob.name.endswith(SETTLEMENT_FILE_SUFFIX):
            continue
        content = container_client.download_blob(blob.name).readall().decode("utf-8")
        try:
            totals_in_file = parse_settlement_file(blob.name, content)
        except MalformedSettlementFileError as error:
            logger.warning("Skipping settlement file %s: %s", blob.name, error)
            continue
        for merchant_id, amount in totals_in_file.items():
            totals[merchant_id] += amount
    return dict(totals)


def build_container_client() -> ContainerClient:
    credential = ChainedTokenCredential(ManagedIdentityCredential(), AzureCliCredential())
    service_client = BlobServiceClient(load_settings().storage_account_url, credential=credential)
    return service_client.get_container_client(SETTLEMENTS_CONTAINER)


def main() -> None:
    totals = total_settlements(build_container_client())
    for merchant_id, total in sorted(totals.items()):
        print(f"{merchant_id},{total}")


if __name__ == "__main__":
    main()
PY
