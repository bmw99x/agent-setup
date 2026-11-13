import { useState } from "react";

import type { OrderStatus } from "./types";
import { useOrders } from "./useOrders";

const STATUS_LABELS: Record<OrderStatus, string> = {
  open: "Open",
  shipped: "Shipped",
  cancelled: "Cancelled",
};

const money = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" });

export function OrdersPage() {
  const [status, setStatus] = useState<OrderStatus>("open");
  const orders = useOrders(status);

  return (
    <section>
      <h1>Orders</h1>
      <label>
        Status
        <select value={status} onChange={(event) => setStatus(event.target.value as OrderStatus)}>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>

      {orders.isPending && <p>Loading orders…</p>}

      {orders.isError && (
        <div role="alert">
          <p>We couldn't load orders.</p>
          <button type="button" onClick={() => orders.refetch()}>
            Try again
          </button>
        </div>
      )}

      {orders.isSuccess && orders.data.length === 0 && (
        <p>No {STATUS_LABELS[status].toLowerCase()} orders.</p>
      )}

      {orders.isSuccess && orders.data.length > 0 && (
        <table aria-label="Orders">
          <thead>
            <tr>
              <th>Order</th>
              <th>Customer</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {orders.data.map((order) => (
              <tr key={order.id}>
                <td>{order.number}</td>
                <td>{order.customerName}</td>
                <td>{money.format(order.totalPence / 100)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
