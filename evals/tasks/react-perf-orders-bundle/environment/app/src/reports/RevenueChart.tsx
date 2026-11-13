import { CartesianGrid, Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";

import type { Order } from "../orders/types";

function monthlyRevenue(orders: Order[]) {
  const totals = new Map<string, number>();
  for (const order of orders) {
    const month = order.placedOn.slice(0, 7);
    totals.set(month, (totals.get(month) ?? 0) + order.total);
  }
  return [...totals].sort(([a], [b]) => a.localeCompare(b)).map(([month, revenue]) => ({ month, revenue }));
}

export function RevenueChart({ orders }: { orders: Order[] }) {
  return (
    <figure>
      <figcaption>Monthly revenue</figcaption>
      <LineChart width={640} height={320} data={monthlyRevenue(orders)}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="revenue" stroke="#2563eb" />
      </LineChart>
    </figure>
  );
}
