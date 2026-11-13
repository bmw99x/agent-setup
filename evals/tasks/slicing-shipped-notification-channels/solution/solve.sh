#!/bin/bash
cat > /app/SLICES.md <<'EOF'
# Order-shipped notification channels

Foundation first (preference storage + channel dispatch seam, email moved onto it, no new behaviour). Then slices 2-4 branch from `main` in parallel.

## Slice 1: Notification channel foundation
Depends on: none
Files:
- migrations/versions/0004_create_notification_preferences.py
- app/notifications/models.py
- app/notifications/channels.py
- app/notifications/repository.py
- app/notifications/dispatcher.py
- app/notifications/email.py
- app/orders/service.py
- migrations/env.py
- tests/notifications/test_dispatcher.py
- tests/orders/test_order_service.py

## Slice 2: Customer reads and changes notification preferences
Depends on: Slice 1
Files:
- app/customers/routes.py
- app/notifications/schemas.py
- app/notifications/service.py
- tests/customers/test_notification_preferences.py

## Slice 3: Order shipped by SMS
Depends on: Slice 1
Files:
- app/notifications/sms.py
- app/notifications/dispatcher.py
- app/notifications/templates.py
- tests/notifications/test_sms.py

## Slice 4: Order shipped by push
Depends on: Slice 1
Files:
- app/notifications/push.py
- app/notifications/dispatcher.py
- tests/notifications/test_push.py
EOF
