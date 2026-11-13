import { Edit } from "@mui/icons-material";
import { useState } from "react";

import type { Order } from "./types";

type Props = { initialOrders: Order[] };

export function OrdersPage({ initialOrders }: Props) {
  const [orders] = useState(initialOrders);
  const [editingId, setEditingId] = useState<string | null>(null);

  return (
    <main>
      <h1>Orders</h1>
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
                  <Edit fontSize="small" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
