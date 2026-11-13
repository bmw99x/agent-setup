#!/bin/bash
cat > /app/SLICES.md <<'EOF'
# Returns (RET-42)

Foundation first; once merged, slices 2-5 branch from `main` in parallel.

## Slice 1: Returns foundation — schema, model, router skeleton
Depends on: none
Files:
- migrations/versions/0004_create_returns.py
- app/returns/__init__.py
- app/returns/models.py
- app/returns/schemas.py
- app/returns/exceptions.py
- app/returns/repository.py
- app/returns/routes.py
- app/main.py
- migrations/env.py
- tests/returns/__init__.py
- tests/returns/test_return_repository.py

Foundation/infra: `returns` + `return_lines` tables, `ReturnStatus`, repository get/add, empty router mounted. No user-visible behaviour.

## Slice 2: Customer requests a return
Depends on: Slice 1
Files:
- app/returns/routes.py
- app/returns/service.py
- app/returns/schemas.py
- tests/returns/test_request_return.py

## Slice 3: Customer cancels a pending return
Depends on: Slice 1
Files:
- app/returns/routes.py
- app/returns/service.py
- tests/returns/test_cancel_return.py

## Slice 4: Staff approves a pending return
Depends on: Slice 1
Files:
- app/returns/routes.py
- app/returns/service.py
- tests/returns/test_approve_return.py

## Slice 5: Staff lists pending returns
Depends on: Slice 1
Files:
- app/returns/routes.py
- app/returns/service.py
- app/returns/repository.py
- tests/returns/test_list_pending_returns.py
EOF
