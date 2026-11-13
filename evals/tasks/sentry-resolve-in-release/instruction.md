# Close out the double-refund bug

The double-refund bug in payments-api is fixed. The fix (the last commit here) went out to production in this morning's deploy. Mark it resolved in Sentry.

Some workers on the previous build keep running until the batch queue drains tonight, and I don't want their errors reopening the issue.

The Sentry CLI is set up on this machine.
