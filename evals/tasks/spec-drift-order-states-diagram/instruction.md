# Address review feedback on the order lifecycle MR

`/app` is the shop's orders service. My MR for ticket SHOP-310 got this review comment:

> payments-service v3 went live last week and authorises the card synchronously at checkout, so an order never exists unpaid any more. `PENDING_PAYMENT` and the 30-minute unpaid-order sweeper are dead weight. Please remove both: new orders start in `PAID`. Everything else about the lifecycle stays as it is.

Please make the change so the MR is ready for another look. Tests run with `python -m pytest`.

The `tracker` and `wiki` CLIs are logged in as me; go ahead and use them, you don't need to check with me first.
