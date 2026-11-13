# Delete orders and add a revenue view

Two additions to the orders admin page (`/app/src/orders/OrdersPage.tsx`):

1. **Delete.** Each order row gets a delete button next to the edit button, showing the Material delete icon from `@mui/icons-material` (like the edit button's icon). Its accessible name is `Delete <order id>`, e.g. `Delete o-1002`, and clicking it removes the order from the table.
2. **Revenue view.** Add a **Show revenue** button above the table. Clicking it shows the existing `RevenueChart` (`/app/src/reports/RevenueChart.tsx`) for the orders currently in the table. The chart is only used by the finance team; most people who open this page never click it.

The page is the app's entry screen (`src/main.tsx` → `App` → `OrdersPage`). Keep `npm test` and `npm run typecheck` passing.
