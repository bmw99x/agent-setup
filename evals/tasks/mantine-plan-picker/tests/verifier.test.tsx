import { MantineProvider } from "@mantine/core";
import { render as rtlRender, fireEvent, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { BillingPage } from "../billing/BillingPage";
import * as pickerModule from "../billing/PlanPicker";
import { PLANS } from "../billing/plans";

const render = (ui: JSX.Element) => rtlRender(<MantineProvider env="test">{ui}</MantineProvider>);

type PickerProps = { plans: typeof PLANS; value: string | null; onChange: (planId: string) => void };
const PlanPicker = (pickerModule as Record<string, unknown>).PlanPicker as (props: PickerProps) => JSX.Element;

function isChecked(element: HTMLElement) {
  return element.getAttribute("aria-checked") === "true" || (element as HTMLInputElement).checked === true;
}

function radioFor(name: string) {
  return screen.getByRole("radio", { name: new RegExp(name, "i") });
}

test("each plan is a radio and the selected plan is checked", () => {
  render(<PlanPicker plans={PLANS} value="growth" onChange={() => {}} />);
  expect(screen.getAllByRole("radio")).toHaveLength(PLANS.length);
  expect(isChecked(radioFor("Growth"))).toBe(true);
  expect(isChecked(radioFor("Starter"))).toBe(false);
  expect(isChecked(radioFor("Enterprise"))).toBe(false);
  for (const feature of ["SSO", "Audit log", "30-day history"]) expect(screen.getAllByText(feature).length).toBeGreaterThan(0);
});

test("clicking anywhere on a card selects that plan", () => {
  const onChange = vi.fn();
  render(<PlanPicker plans={PLANS} value="growth" onChange={onChange} />);
  fireEvent.click(screen.getByText("Dedicated account manager"));
  expect(onChange).toHaveBeenCalledWith("enterprise");
});

test("billing page starts on the account plan and tracks the selection", () => {
  render(<BillingPage account={{ name: "Acme Ltd", billingEmail: "ap@acme.test", planId: "starter" }} />);
  expect(screen.queryByText(/coming soon/i)).toBeNull();
  expect(isChecked(radioFor("Starter"))).toBe(true);
  fireEvent.click(radioFor("Growth"));
  expect(isChecked(radioFor("Growth"))).toBe(true);
  expect(isChecked(radioFor("Starter"))).toBe(false);
});
