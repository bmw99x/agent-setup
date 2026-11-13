import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { OrdersPage } from "./OrdersPage";
import { SAMPLE_ORDERS } from "./sampleOrders";

test("lists orders and marks the one being edited", () => {
  render(<OrdersPage initialOrders={SAMPLE_ORDERS} />);
  fireEvent.click(screen.getByRole("button", { name: "Edit o-1002" }));
  expect(screen.getByText("Contoso").closest("tr")?.className).toBe("editing");
});
