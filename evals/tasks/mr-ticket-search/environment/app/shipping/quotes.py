"""Carrier delivery quotes for checkout."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Quote:
    carrier: str
    price_pence: int


class CarrierTimeout(Exception):
    """The carrier did not answer in time."""


def fetch_quotes(carriers: Iterable[str], request_quote: Callable[[str], Quote]) -> list[Quote]:
    """Ask every carrier for a quote; carriers that time out are left out."""
    quotes = []
    for carrier in carriers:
        try:
            quotes.append(request_quote(carrier))
        except CarrierTimeout:
            continue
    return quotes
