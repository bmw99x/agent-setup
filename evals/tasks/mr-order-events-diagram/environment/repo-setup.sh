set -e
cd /app
git init -q --bare /srv/git/shop/orders.git
git init -q
git remote add origin git@gitlab.example.test:shop/orders.git
git add .gitignore README.md orders tests
git commit -q -m "feat(checkout): place orders through a single entry point (ORD-61)"
git push -q -u origin main
git remote set-head origin -a >/dev/null
git checkout -q -b ord-77-order-placed-event

cat > orders/events.py <<'PY'
"""Domain events published by the orders service."""

import json
from dataclasses import asdict, dataclass
from typing import Protocol

ORDER_EVENTS_QUEUE = "order-events"


@dataclass(frozen=True)
class OrderPlaced:
    order_id: str
    email: str
    total_pence: int
    type: str = "order.placed"

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class EventPublisher(Protocol):
    def publish(self, queue: str, message: str) -> None: ...
PY
git add orders/events.py
git commit -q -m "feat(checkout): add order.placed event (ORD-77)"

cat > orders/checkout.py <<'PY'
"""Order placement."""

from dataclasses import dataclass
from typing import Protocol

from orders.events import ORDER_EVENTS_QUEUE, EventPublisher, OrderPlaced


@dataclass(frozen=True)
class Order:
    id: str
    email: str
    total_pence: int


class OrderStore(Protocol):
    def save(self, order: Order) -> None: ...


def place_order(order: Order, store: OrderStore, events: EventPublisher) -> None:
    """Save the order and announce it; notifications-service sends the confirmation email."""
    store.save(order)
    events.publish(ORDER_EVENTS_QUEUE, OrderPlaced(order.id, order.email, order.total_pence).to_json())
PY
cat > tests/test_checkout.py <<'PY'
import json

from orders.checkout import Order, place_order


class FakeStore:
    def __init__(self):
        self.saved = []

    def save(self, order):
        self.saved.append(order)


class FakePublisher:
    def __init__(self):
        self.published = []

    def publish(self, queue, message):
        self.published.append((queue, json.loads(message)))


def test_place_order_saves_and_publishes_order_placed():
    store, events = FakeStore(), FakePublisher()
    place_order(Order("o-1", "ana@example.com", 1250), store, events)
    assert store.saved
    assert events.published == [
        ("order-events", {"order_id": "o-1", "email": "ana@example.com", "total_pence": 1250, "type": "order.placed"})
    ]
PY
git add orders/checkout.py tests/test_checkout.py
git commit -q -m "refactor(checkout): publish order.placed instead of calling notifications-service"
git push -q -u origin ord-77-order-placed-event

mkdir -p docs
cat > docs/events.md <<'MD'
# Events

## `order.placed` (queue `order-events`)

Published by `place_order` after the order is saved.

| field | type |
|---|---|
| `order_id` | string |
| `email` | string |
| `total_pence` | integer |
| `type` | `"order.placed"` |
MD
git add docs/events.md
git commit -q -m "docs(events): describe the order.placed payload"
