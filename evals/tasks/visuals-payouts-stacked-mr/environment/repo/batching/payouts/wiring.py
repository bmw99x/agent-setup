import os
import sqlite3
from pathlib import Path

from payouts.bank import BankClient
from payouts.batch import BatchQueue
from payouts.db import UnitOfWork
from payouts.ledger import LedgerRepository
from payouts.service import PayoutService


def _uow() -> UnitOfWork:
    return UnitOfWork(sqlite3.connect(os.environ["PAYOUTS_DB"]))


def _queue() -> BatchQueue:
    return BatchQueue(Path(os.environ["PAYOUTS_SPOOL"]))


def payout_service() -> PayoutService:
    uow = _uow()
    return PayoutService(uow, LedgerRepository(uow), _queue())


def batch_worker_parts() -> tuple[UnitOfWork, LedgerRepository, BatchQueue, BankClient]:
    uow = _uow()
    return uow, LedgerRepository(uow), _queue(), BankClient(os.environ["BANK_URL"], os.environ["BANK_API_KEY"])
