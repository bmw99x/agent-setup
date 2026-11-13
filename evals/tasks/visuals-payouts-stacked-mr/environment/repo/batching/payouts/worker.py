"""Runs every five minutes: sends queued payouts to the bank."""

from payouts.wiring import batch_worker_parts


def flush_batch() -> int:
    uow, ledger, queue, bank = batch_worker_parts()
    sent = 0
    for payout_id in queue.drain():
        account_id, amount_pence = uow.execute(
            "SELECT account_id, amount_pence FROM payouts WHERE id = ?", (payout_id,)
        ).fetchone()
        ledger.mark_sent(payout_id, bank.send_transfer(account_id, amount_pence, reference=payout_id))
        uow.commit()
        sent += 1
    return sent
