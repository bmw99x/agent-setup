"""Refunds, triggered by the acquirer's charge.refund_requested webhook."""

from dataclasses import dataclass
from decimal import Decimal

from payments.gateway import Gateway


class RefundAmountError(Exception):
    pass


@dataclass
class Charge:
    id: str
    captured: Decimal
    refund_id: str | None = None


def validate_amount(charge: Charge, amount: Decimal) -> None:
    if amount > charge.captured:
        raise RefundAmountError(f"refund of {amount} exceeds captured amount {charge.captured}")


def issue_refund(gateway: Gateway, charge: Charge, amount: Decimal) -> str:
    validate_amount(charge, amount)
    if charge.refund_id:
        return charge.refund_id
    charge.refund_id = gateway.create_refund(charge.id, amount)
    return charge.refund_id
