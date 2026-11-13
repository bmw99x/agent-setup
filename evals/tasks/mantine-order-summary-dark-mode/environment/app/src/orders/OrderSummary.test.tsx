import { screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { render } from "../test-utils";
import { OrderSummary } from "./OrderSummary";

test("shows every line and the total", () => {
  render(
    <OrderSummary
      order={{
        number: "A-1001",
        lines: [
          { id: "1", description: "Desk lamp", amountPence: 3499 },
          { id: "2", description: "Delivery", amountPence: 499 },
        ],
      }}
    />,
  );
  expect(screen.getByText("Desk lamp")).toBeTruthy();
  expect(screen.getByText("£39.98")).toBeTruthy();
});
