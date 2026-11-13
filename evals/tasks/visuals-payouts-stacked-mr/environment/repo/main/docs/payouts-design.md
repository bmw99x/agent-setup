# Payouts: design

Sellers request a payout of their available balance from the dashboard. The dashboard calls `POST /payouts`.

## Flow

1. The API validates the request and the payout limit.
2. The amount is reserved on the seller's ledger so it cannot be paid out twice.
3. The bank transfer goes to the partner bank.
4. The ledger entry is marked sent.

## Limits

A single payout may not exceed **£10,000**. Larger requests are rejected with 422 and the seller is asked to split
them.

## Delivery

- !42 lays the scaffolding: the route, `PayoutService`, the ledger repository, and a synchronous bank call.
- !43, stacked on !42, takes the bank call off the request path: requests are queued and a worker sends them in
  batches. **!43 is the version that ships**; review the request path as it stands there. !42 only exists to keep
  the diff readable.
