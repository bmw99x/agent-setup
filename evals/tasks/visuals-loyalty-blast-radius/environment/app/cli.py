"""Command-line entry points for the loyalty service: `python cli.py <command> <args...>`."""

import sys
from datetime import date

from loyalty.accrual import AccrualService
from loyalty.campaigns import BonusCampaign
from loyalty.checkout import CheckoutHandler
from loyalty.expiry import expire_points
from loyalty.giftcards import GiftCard, GiftCardService
from loyalty.ledger import PointsLedger
from loyalty.models import Order
from loyalty.preview import preview_points
from loyalty.statement import statement_lines

LEDGER = PointsLedger()
REPLAYABLE_STEPS = ("accrue",)


def cmd_checkout(member_id: str, total_pence: str, tier: str) -> None:
    handler = CheckoutHandler(AccrualService(LEDGER))
    print(handler.complete(Order(member_id, int(total_pence), tier)))


def cmd_preview(basket_pence: str, tier: str) -> None:
    print(preview_points(int(basket_pence), tier))


def cmd_campaign(code: str, member_id: str, amount_pence: str) -> None:
    print(BonusCampaign(LEDGER).apply(code, member_id, int(amount_pence)))


def cmd_replay(step: str, member_id: str, total_pence: str, tier: str) -> None:
    """Support tool: re-run one accrual step by name for an order that failed, e.g. `replay accrue m-1 2500 gold`."""
    if step not in REPLAYABLE_STEPS:
        raise SystemExit(f"cannot replay {step!r}; choose from {REPLAYABLE_STEPS}")
    service = AccrualService(LEDGER)
    print(getattr(service, step)(Order(member_id, int(total_pence), tier)))


def cmd_giftcard(code: str, balance_pence: str, amount_pence: str) -> None:
    service = GiftCardService()
    card = service.redeem(GiftCard(code, int(balance_pence)), int(amount_pence))
    print(f"{card.code}: {card.balance_pence} left, {service.points_for(card)} points")


def cmd_statement(member_id: str) -> None:
    print("\n".join(statement_lines(LEDGER, member_id)))


def cmd_expire() -> None:
    print(f"expired {expire_points(LEDGER, date.today())} entries")


COMMANDS = {
    "checkout": cmd_checkout,
    "preview": cmd_preview,
    "campaign": cmd_campaign,
    "replay": cmd_replay,
    "giftcard": cmd_giftcard,
    "statement": cmd_statement,
    "expire": cmd_expire,
}

if __name__ == "__main__":
    COMMANDS[sys.argv[1]](*sys.argv[2:])
