"""Use cases for loyalty points."""

from app.domain.loyalty import points_for


class LoyaltyService:
    def __init__(self, accounts):
        self._accounts = accounts

    def balance(self, customer_id):
        return self._accounts.get(customer_id).points

    def award_for_order(self, customer_id, order_id, total_cents):
        account = self._accounts.get(customer_id)
        earned = points_for(total_cents)
        account.points += earned
        self._accounts.save(account, earned, f"order {order_id}")
        return earned

    def redeem(self, customer_id, points):
        account = self._accounts.get(customer_id)
        account.redeem(points)
        self._accounts.save(account, -points, "redemption")
        return account.points
