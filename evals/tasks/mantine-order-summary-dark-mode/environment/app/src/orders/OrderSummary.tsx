import { Text, Title } from "@mantine/core";

import { formatMoney } from "./money";
import classes from "./OrderSummary.module.css";
import type { Order } from "./types";

export function OrderSummary({ order }: { order: Order }) {
  const total = order.lines.reduce((sum, line) => sum + line.amountPence, 0);

  return (
    <div className={classes.panel}>
      <Title order={3} style={{ color: "#1a1b1e" }}>
        Order {order.number}
      </Title>
      <div className={classes.lines}>
        {order.lines.map((line) => (
          <div key={line.id} className={classes.line}>
            <Text>{line.description}</Text>
            <Text className={classes.amount}>{formatMoney(line.amountPence)}</Text>
          </div>
        ))}
      </div>
      <div className={classes.totalRow}>
        <Text fw={700}>Total</Text>
        <Text fw={700} className={classes.amount}>
          {formatMoney(total)}
        </Text>
      </div>
      <Text size="sm" style={{ color: "#868e96" }}>
        Prices include VAT.
      </Text>
    </div>
  );
}
