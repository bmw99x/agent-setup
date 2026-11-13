# Design: order lifecycle (SHOP-310)

Status: approved (2026-10-20).

![Order lifecycle](../diagrams/order-lifecycle.svg)

## States

- `PENDING_PAYMENT` — created at checkout. The payment provider confirms asynchronously via a
  webhook, so an order exists before it is paid.
- `PAID` — payment captured; the warehouse may start picking.
- `PACKED`, `SHIPPED`, `DELIVERED` — fulfilment progress.
- `CANCELLED` — terminal.

## Unpaid orders

A sweeper job cancels orders still in `PENDING_PAYMENT` 30 minutes after checkout, releasing their
reserved stock.

## Cancellation

Customers can cancel until the order is `PACKED`. After that, cancellation is refused and support
handles it as a return.
