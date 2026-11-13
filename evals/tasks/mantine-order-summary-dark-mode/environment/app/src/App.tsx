import { Container, Group, Title } from "@mantine/core";

import { OrderSummary } from "./orders/OrderSummary";

const order = {
  number: "A-1001",
  lines: [
    { id: "1", description: "Desk lamp", amountPence: 3499 },
    { id: "2", description: "Delivery", amountPence: 499 },
  ],
};

export function App() {
  return (
    <Container size="md" py="xl">
      <Group justify="space-between" mb="lg">
        <Title order={2}>Checkout</Title>
      </Group>
      <OrderSummary order={order} />
    </Container>
  );
}
