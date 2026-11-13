import { MantineProvider } from "@mantine/core";
import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { OrderSummary } from "../orders/OrderSummary";
import { theme } from "../theme";

const order = {
  number: "B-2002",
  lines: [
    { id: "1", description: "Monitor arm", amountPence: 5999 },
    { id: "2", description: "Cable tidy", amountPence: 1250 },
  ],
};

function renderDark() {
  return render(
    <MantineProvider theme={theme} env="test" forceColorScheme="dark">
      <OrderSummary order={order} />
    </MantineProvider>,
  );
}

test("order summary shows every line, the total and the VAT note", () => {
  renderDark();
  expect(screen.getByText(/B-2002/)).toBeTruthy();
  expect(screen.getByText("Monitor arm")).toBeTruthy();
  expect(screen.getByText("£59.99")).toBeTruthy();
  expect(screen.getByText("£72.49")).toBeTruthy();
  expect(screen.getByText(/Prices include VAT/)).toBeTruthy();
});

test("panel surface is a Mantine Paper or Card", () => {
  const { container } = renderDark();
  const surface = container.querySelector(".mantine-Paper-root, .mantine-Card-root");
  expect(surface, "no Paper/Card surface rendered").not.toBeNull();
  expect(surface!.textContent).toContain("Monitor arm");
});
