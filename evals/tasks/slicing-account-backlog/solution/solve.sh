#!/bin/bash
cat > /app/SLICES.md <<'EOF'
# Sprint backlog

No shared core between the three items, so each is its own merge request from `main`.

## Slice 1: Delivery instructions on the customer profile
Depends on: none
Files:
- migrations/versions/0004_add_customer_delivery_instructions.py
- app/customers/models.py
- app/customers/schemas.py
- tests/customers/test_customer_routes.py

## Slice 2: Staff list overdue deliveries
Depends on: none
Files:
- app/orders/routes.py
- app/orders/service.py
- app/orders/repository.py
- app/orders/schemas.py
- tests/orders/test_overdue_deliveries.py

## Slice 3: Customer downloads order history as CSV
Depends on: none
Files:
- app/orders/routes.py
- app/orders/service.py
- app/orders/csv_export.py
- tests/orders/test_order_history_csv.py
EOF
