import { Button, Paper, Stack, Text, Title } from "@mantine/core";

import { PageHeader } from "../layout/PageHeader";
import type { Account } from "./account";

export function BillingPage({ account }: { account: Account }) {
  return (
    <>
      <PageHeader title="Billing" subtitle={account.name} actions={<Button variant="default">Download invoices</Button>} />
      <Stack gap="xl">
        <section>
          <Title order={3} mb="sm">
            Plan
          </Title>
          <Text c="dimmed">Plan selection coming soon.</Text>
        </section>
        <Paper withBorder p="md">
          <Title order={3} mb="xs">
            Billing contact
          </Title>
          <Text>{account.billingEmail}</Text>
        </Paper>
      </Stack>
    </>
  );
}
