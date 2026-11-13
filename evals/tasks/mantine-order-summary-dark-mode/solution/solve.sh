#!/bin/bash
set -euo pipefail
cd /app
cat > src/orders/OrderSummary.module.css <<'CSS'
.amount {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
CSS
cat > src/orders/OrderSummary.tsx <<'TSX'
import { Divider, Group, Paper, Stack, Text, Title } from "@mantine/core";

import { formatMoney } from "./money";
import classes from "./OrderSummary.module.css";
import type { Order } from "./types";

export function OrderSummary({ order }: { order: Order }) {
  const total = order.lines.reduce((sum, line) => sum + line.amountPence, 0);

  return (
    <Paper withBorder radius="md" p="md" maw={360}>
      <Stack gap="sm">
        <Title order={3}>Order {order.number}</Title>
        <Stack gap="xs">
          {order.lines.map((line) => (
            <Group key={line.id} justify="space-between" gap="md" wrap="nowrap">
              <Text>{line.description}</Text>
              <Text className={classes.amount}>{formatMoney(line.amountPence)}</Text>
            </Group>
          ))}
        </Stack>
        <Divider />
        <Group justify="space-between">
          <Text fw={700}>Total</Text>
          <Text fw={700} className={classes.amount}>
            {formatMoney(total)}
          </Text>
        </Group>
        <Text size="sm" c="dimmed">
          Prices include VAT.
        </Text>
      </Stack>
    </Paper>
  );
}
TSX
