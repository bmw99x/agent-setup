# Tests for the orders page

The back-office orders page (`/app/src/orders/OrdersPage.tsx`) has no tests, and it broke twice last month. Add tests for it.

What it does:

- Lists the orders for a status (open by default). Staff can switch the status to see shipped or cancelled orders.
- Says so when there are no orders with that status.
- If the orders can't be loaded it shows an error, and **Try again** reloads them.

The tests run in CI, which can't reach the orders API. Don't change the page or its hook. `npm test` must pass.
