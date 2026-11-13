import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, test } from "vitest";

import { OrdersPage } from "../orders/OrdersPage";
import { SAMPLE_ORDERS } from "../orders/sampleOrders";

test("delete button removes the order", () => {
  render(<OrdersPage initialOrders={SAMPLE_ORDERS} />);
  fireEvent.click(screen.getByRole("button", { name: "Delete o-1002" }));
  expect(screen.queryByText("Contoso")).toBeNull();
  expect(screen.getByText("Northwind")).toBeTruthy();
  expect(screen.getByText("Fabrikam")).toBeTruthy();
});

test("delete button shows a Material delete icon", () => {
  render(<OrdersPage initialOrders={SAMPLE_ORDERS} />);
  const button = screen.getByRole("button", { name: "Delete o-1001" });
  expect(within(button).getByTestId(/^Delete\w*Icon$/)).toBeTruthy();
});

test("show revenue reveals the revenue chart", async () => {
  render(<OrdersPage initialOrders={SAMPLE_ORDERS} />);
  expect(screen.queryByText("Monthly revenue")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Show revenue" }));
  expect(await screen.findByText("Monthly revenue", undefined, { timeout: 15000 })).toBeTruthy();
}, 20000);
