from dataclasses import dataclass

from payouts.bank import BankClient
from payouts.db import UnitOfWork
from payouts.ledger import LedgerRepository, Payout

MAX_PAYOUT_PENCE = 1_000_000


class PayoutRejected(Exception):
    pass


@dataclass
class PayoutService:
    uow: UnitOfWork
    ledger: LedgerRepository
    bank: BankClient

    def request(self, account_id: str, amount_pence: int) -> Payout:
        if amount_pence > MAX_PAYOUT_PENCE:
            raise PayoutRejected(f"payouts are limited to {MAX_PAYOUT_PENCE} pence")
        payout = self.ledger.reserve(account_id, amount_pence)
        transfer_id = self.bank.send_transfer(account_id, amount_pence, reference=payout.id)
        self.ledger.mark_sent(payout.id, transfer_id)
        self.uow.commit()
        return payout
