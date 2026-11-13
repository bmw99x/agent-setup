#!/bin/bash
set -euo pipefail
cd /app
cat > src/billing/PlanPicker.module.css <<'CSS'
.card {
  cursor: pointer;
  transition: transform 150ms ease, box-shadow 150ms ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--mantine-shadow-md);
}

.card[data-checked] {
  border-color: var(--mantine-color-blue-filled);
}

.price {
  white-space: nowrap;
}
CSS
cat > src/billing/PlanPicker.tsx <<'TSX'
import { List, Radio, SimpleGrid, Stack, Text, Title } from "@mantine/core";

import classes from "./PlanPicker.module.css";
import type { Plan } from "./plans";

type PlanPickerProps = {
  plans: Plan[];
  value: string | null;
  onChange: (planId: string) => void;
};

export function PlanPicker({ plans, value, onChange }: PlanPickerProps) {
  return (
    <Radio.Group value={value} onChange={onChange} aria-label="Plan">
      <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md">
        {plans.map((plan) => (
          <Radio.Card key={plan.id} value={plan.id} withBorder radius="md" p="lg" className={classes.card}>
            <Stack gap="sm">
              <Title order={4}>{plan.name}</Title>
              <Text fw={700} fz="lg" className={classes.price}>
                {plan.monthlyPrice} / month
              </Text>
              <List size="sm" spacing="xs">
                {plan.features.map((feature) => (
                  <List.Item key={feature}>{feature}</List.Item>
                ))}
              </List>
            </Stack>
          </Radio.Card>
        ))}
      </SimpleGrid>
    </Radio.Group>
  );
}
TSX
cat > src/billing/BillingPage.tsx <<'TSX'
import { Button, Paper, Stack, Text, Title } from "@mantine/core";
import { useState } from "react";

import { PageHeader } from "../layout/PageHeader";
import type { Account } from "./account";
import { PlanPicker } from "./PlanPicker";
import { PLANS } from "./plans";

export function BillingPage({ account }: { account: Account }) {
  const [planId, setPlanId] = useState<string | null>(account.planId);

  return (
    <>
      <PageHeader title="Billing" subtitle={account.name} actions={<Button variant="default">Download invoices</Button>} />
      <Stack gap="xl">
        <section>
          <Title order={3} mb="sm">
            Plan
          </Title>
          <PlanPicker plans={PLANS} value={planId} onChange={setPlanId} />
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
TSX
