#!/bin/bash
# Reference: move the loyalty modules, and keep the OrderPlaced subscription registered by importing the
# loyalty handlers explicitly at startup (the subscribers/ autodiscovery only scans app/subscribers/).
set -euo pipefail
cd /app
mkdir -p app/loyalty
touch app/loyalty/__init__.py
git mv app/domain/loyalty.py app/loyalty/domain.py
git mv app/repositories/loyalty_repository.py app/loyalty/repository.py
git mv app/services/loyalty_service.py app/loyalty/service.py
git mv app/subscribers/loyalty.py app/loyalty/handlers.py
grep -rl --include=*.py -e app.domain.loyalty -e app.repositories.loyalty_repository -e app.services.loyalty_service app tests \
  | xargs sed -i -e 's/app\.domain\.loyalty/app.loyalty.domain/g' \
                 -e 's/app\.repositories\.loyalty_repository/app.loyalty.repository/g' \
                 -e 's/app\.services\.loyalty_service/app.loyalty.service/g'
cat > app/events/discovery.py <<'PY'
"""Startup hook that loads the event subscribers."""

import importlib
import pkgutil

from app import subscribers

# Subscriber modules outside app/subscribers/ that must be imported for their @subscribe to register.
CONTEXT_SUBSCRIBERS = ("app.loyalty.handlers",)

_done = False


def autodiscover():
    global _done
    if _done:
        return
    for module in pkgutil.iter_modules(subscribers.__path__):
        importlib.import_module(f"{subscribers.__name__}.{module.name}")
    for name in CONTEXT_SUBSCRIBERS:
        importlib.import_module(name)
    _done = True
PY
cat >> tests/test_orders.py <<'PY'


def test_placed_order_awards_loyalty_points():
    router = create_app()
    router.handle("POST", "/orders", {"customerId": 8, "customerEmail": "bo@example.com", "totalCents": 2500})
    _, body = router.handle("GET", "/customers/8/loyalty")
    assert body["points"] == 25
PY
