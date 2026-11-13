# Tell people when a refund is issued

Staff issue refunds through `POST /refunds/{refund_id}/issue`, which calls `RefundService.issue` in `/app/app/refunds/service.py`. Today nobody hears about it. When a refund is issued:

- the customer gets an email telling them the refund amount and the order it is for;
- finance's ledger gets a `refund.issued` message on the queue carrying the refund id, order id and amount.

Our email sender and queue publisher live in `app/messaging/`. Nothing must be sent when a refund can't be issued. Keep the tests in `/app/tests` passing.
