from dataclasses import dataclass


@dataclass
class GiftCard:
    code: str
    balance_pence: int


class GiftCardService:
    def points_for(self, card: GiftCard) -> int:
        """Gift card purchases earn no loyalty points; kept so the receipt can print a points line."""
        return 0

    def redeem(self, card: GiftCard, amount_pence: int) -> GiftCard:
        if amount_pence > card.balance_pence:
            raise ValueError("insufficient gift card balance")
        return GiftCard(card.code, card.balance_pence - amount_pence)
