import { Container } from "@mantine/core";

import { BillingPage } from "./billing/BillingPage";

export function App() {
  return (
    <Container size="lg" py="xl">
      <BillingPage account={{ name: "Acme Ltd", billingEmail: "ap@acme.test", planId: "growth" }} />
    </Container>
  );
}
