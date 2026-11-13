"""The one place that builds HTTP clients for the supplier API."""

from tidyhttp import Client

from app.settings import SUPPLIER_API_TIMEOUT_SECONDS, SUPPLIER_API_URL


def supplier_client() -> Client:
    return Client(SUPPLIER_API_URL, timeout=SUPPLIER_API_TIMEOUT_SECONDS)
