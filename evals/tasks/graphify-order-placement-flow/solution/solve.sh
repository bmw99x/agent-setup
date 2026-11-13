#!/bin/bash
set -euo pipefail
cat > /app/ORDER_FLOW.md <<'MD'
# POST /orders — order placement flow

```mermaid
flowchart LR
  Client([Client]) -->|POST /orders JSON| Route
  subgraph RouteLayer[Route layer]
    Route["POST /orders<br/>place_order_endpoint"]
  end
  subgraph ServiceLayer[Service layer]
    Svc["OrderService.place_order"]
  end
  subgraph RepoLayer[Repository layer]
    Inv["InventoryRepository.reserve"]
    Repo["OrderRepository.add"]
    Ledger["SalesLedgerRepository.book"]
  end
  subgraph AdapterLayer[Adapter layer]
    GW["payments.get_gateway()"]
    Card["card_gateway.Gateway.charge"]
    Inv2["invoice_gateway.Gateway.charge"]
    Mail["Mailer.send"]
  end
  subgraph EventLayer[Domain events]
    Bus{{"events.bus.publish(OrderPlaced)"}}
    Confirm["notifications.handlers.send_order_confirmation"]
    Sale["analytics.handlers.record_sale"]
  end
  Route -->|PlaceOrderRequest.to_command| Svc
  Svc -->|1 reserve lines| Inv
  Svc -->|2 charge total| GW
  GW -.->|PAYMENT_PROVIDER=card ?| Card
  GW -.->|PAYMENT_PROVIDER=invoice ?| Inv2
  Svc -->|3 add order| Repo
  Svc -->|4 publish OrderPlaced| Bus
  Bus -->|subscriber| Confirm
  Bus -->|subscriber| Sale
  Confirm --> Mail
  Sale --> Ledger
  Inv --> Stock[(stock)]
  Repo --> Orders[(orders)]
  Repo --> Lines[(order_lines)]
  Ledger --> SL[(sales_ledger)]
```

- Entry: `app/api/routes.py:16` (`place_order_endpoint`), registered by `build_router`.
- Layer path: route → `OrderService.place_order` (`app/services/order_service.py:14`) → repositories / payment adapter.
- Data shapes: JSON body → `PlaceOrderRequest` → `PlaceOrderCommand` → `Order` → `OrderPlaced` → `OrderResponse`.
- Tables written: `stock` (reserved), `orders`, `order_lines`, `sales_ledger`.
- Side effects: card/invoice charge; confirmation email queued in `Mailer.OUTBOX`; sales ledger row.
- Surprise: subscribers are not imported anywhere explicitly — `events/wiring.load_subscribers()` imports every
  `*.handlers` module at startup and `@subscribe(OrderPlaced)` registers them at import time.
- Open question: which provider `PAYMENT_PROVIDER` selects in each deployment (not in the repo).
- Smells: the stock reservation is not released if the charge fails; `app/legacy/checkout_v1.py` is dead code.
MD
