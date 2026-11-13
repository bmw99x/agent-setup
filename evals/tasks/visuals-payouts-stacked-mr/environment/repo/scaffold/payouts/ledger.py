import uuid
from dataclasses import dataclass

from payouts.db import UnitOfWork


@dataclass(frozen=True)
class Payout:
    id: str
    account_id: str
    amount_pence: int
    status: str


@dataclass
class LedgerRepository:
    uow: UnitOfWork

    def reserve(self, account_id: str, amount_pence: int) -> Payout:
        """Move the amount from available to reserved; fails if the balance is short."""
        payout = Payout(str(uuid.uuid4()), account_id, amount_pence, "reserved")
        updated = self.uow.execute(
            "UPDATE balances SET available = available - ?, reserved = reserved + ? "
            "WHERE account_id = ? AND available >= ?",
            (amount_pence, amount_pence, account_id, amount_pence),
        )
        if updated.rowcount != 1:
            raise InsufficientBalance(account_id)
        self.uow.execute(
            "INSERT INTO payouts (id, account_id, amount_pence, status) VALUES (?, ?, ?, ?)",
            (payout.id, account_id, amount_pence, payout.status),
        )
        return payout

    def mark_sent(self, payout_id: str, transfer_id: str) -> None:
        self.uow.execute(
            "UPDATE payouts SET status = 'sent', transfer_id = ? WHERE id = ?", (transfer_id, payout_id)
        )


class InsufficientBalance(Exception):
    pass
