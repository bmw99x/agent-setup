#!/bin/bash
set -euo pipefail
cd /app
cat > src/orders/OrdersPage.tsx <<'TS'
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import { lazy, Suspense, useState } from "react";

import type { Order } from "./types";

// Only finance opens the revenue view, so recharts loads on demand.
const RevenueChart = lazy(() =>
  import("../reports/RevenueChart").then((module) => ({ default: module.RevenueChart })),
);

type Props = { initialOrders: Order[] };

export function OrdersPage({ initialOrders }: Props) {
  const [orders, setOrders] = useState(initialOrders);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showRevenue, setShowRevenue] = useState(false);

  const deleteOrder = (id: string) => setOrders((current) => current.filter((order) => order.id !== id));

  return (
    <main>
      <h1>Orders</h1>
      <button type="button" onClick={() => setShowRevenue(true)}>
        Show revenue
      </button>
      {showRevenue && (
        <Suspense fallback={<p>Loading chart…</p>}>
          <RevenueChart orders={orders} />
        </Suspense>
      )}
      <table>
        <thead>
          <tr>
            <th>Order</th>
            <th>Customer</th>
            <th>Total</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id} className={order.id === editingId ? "editing" : undefined}>
              <td>{order.id}</td>
              <td>{order.customer}</td>
              <td>{order.total}</td>
              <td>
                <button type="button" aria-label={`Edit ${order.id}`} onClick={() => setEditingId(order.id)}>
                  <EditIcon fontSize="small" />
                </button>
                <button type="button" aria-label={`Delete ${order.id}`} onClick={() => deleteOrder(order.id)}>
                  <DeleteIcon fontSize="small" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
TS
