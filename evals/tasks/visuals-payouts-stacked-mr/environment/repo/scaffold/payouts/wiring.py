import os
import sqlite3

from payouts.bank import BankClient
from payouts.db import UnitOfWork
from payouts.ledger import LedgerRepository
from payouts.service import PayoutService


def payout_service() -> PayoutService:
    uow = UnitOfWork(sqlite3.connect(os.environ["PAYOUTS_DB"]))
    bank = BankClient(os.environ["BANK_URL"], os.environ["BANK_API_KEY"])
    return PayoutService(uow, LedgerRepository(uow), bank)
