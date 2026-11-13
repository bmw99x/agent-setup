# Design: order cancellation

Status: approved (2026-09-20).

`POST /orders/{id}/cancel` moves a placed order to `cancelled`. Cancelling an order that is
already cancelled returns `409 Conflict` rather than succeeding silently, so double-clicks in the
back-office surface as an error instead of a second refund.

Refunds are triggered asynchronously by the payments service listening for `order.cancelled`.
