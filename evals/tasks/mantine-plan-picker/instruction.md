# Plan picker on the billing page

The billing page (`src/billing/BillingPage.tsx`) still says "Plan selection coming soon." Replace that with a plan picker.

- Add `src/billing/PlanPicker.tsx` exporting `PlanPicker({ plans, value, onChange })`: `plans: Plan[]` (from `src/billing/plans.ts`), `value: string | null` (the selected plan id) and `onChange: (planId: string) => void`.
- Each plan is a card with its name, its price as e.g. "£25 / month", and its features as a list. Three cards side by side on desktop, stacked on phones.
- The whole card is clickable and shows a pointer cursor. On hover a card lifts slightly with a shadow. The selected card gets a blue border.
- The price must never wrap onto two lines.
- Picking a plan is a single choice; screen-reader users should hear it as one, with the selected plan announced as selected.
- `BillingPage` keeps the selected plan in state, starting from the account's current plan (`account.planId`). Use `PLANS`.

Keep `npm test` and `npm run typecheck` passing.
