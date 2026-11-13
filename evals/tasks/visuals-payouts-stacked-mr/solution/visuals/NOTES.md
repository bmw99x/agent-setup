# POST /payouts request path

- Drawn from **!43** (`feature/payout-batching`), stacked on !42: the design doc says !43 is the version that ships.
  In !42 the bank transfer runs inside the request before the commit; in !43 the request reserves, commits, then
  enqueues the payout id, and `worker.flush_batch` sends transfers later.
- Doc vs code: the doc says a payout may not exceed £10,000; `MAX_PAYOUT_PENCE = 500_000` in !43 is £5,000
  (!42 had 1_000_000).
