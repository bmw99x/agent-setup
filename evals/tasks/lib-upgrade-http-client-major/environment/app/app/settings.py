import os

SUPPLIER_API_URL = os.environ.get("SUPPLIER_API_URL", "https://api.supplier.example/v2")
SUPPLIER_API_TIMEOUT_SECONDS = float(os.environ.get("SUPPLIER_API_TIMEOUT_SECONDS", "15"))
SYNC_PAGE_COUNT = int(os.environ.get("SYNC_PAGE_COUNT", "40"))
