from dataclasses import dataclass

from payouts.batch import BatchQueue
from payouts.db import UnitOfWork
from payouts.ledger import LedgerRepository, Payout

MAX_PAYOUT_PENCE = 500_000


class PayoutRejected(Exception):
    pass


@dataclass
class PayoutService:
    uow: UnitOfWork
    ledger: LedgerRepository
    queue: BatchQueue

    def request(self, account_id: str, amount_pence: int) -> Payout:
        if amount_pence > MAX_PAYOUT_PENCE:
            raise PayoutRejected(f"payouts are limited to {MAX_PAYOUT_PENCE} pence")
        payout = self.ledger.reserve(account_id, amount_pence)
        self.uow.commit()
        # Enqueue only after the commit: the worker must never pick up a reservation that could still roll back.
        self.queue.enqueue(payout.id)
        return payout
