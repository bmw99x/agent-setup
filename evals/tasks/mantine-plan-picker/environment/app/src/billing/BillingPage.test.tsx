import { screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { render } from "../test-utils";
import { BillingPage } from "./BillingPage";

test("shows the billing contact", () => {
  render(<BillingPage account={{ name: "Acme Ltd", billingEmail: "ap@acme.test", planId: "growth" }} />);
  expect(screen.getByText("ap@acme.test")).toBeTruthy();
});
