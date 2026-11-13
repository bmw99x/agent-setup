#!/bin/bash
set -euo pipefail
cd /app
mkdir -p src/test/msw
cat > src/test/msw/server.ts <<'TS'
import { setupServer } from "msw/node";

export const server = setupServer();
TS
cat > src/setupTests.ts <<'TS'
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "./test/msw/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
TS
cat > src/orders/OrdersPage.test.tsx <<'TS'
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { expect, test } from "vitest";

import { server } from "../test/msw/server";
import { OrdersPage } from "./OrdersPage";
import type { Order } from "./types";

const openOrder: Order = { id: "o1", number: "ORD-1001", customerName: "Ada Lovelace", totalPence: 1250, status: "open" };
const shippedOrder: Order = { id: "o2", number: "ORD-1002", customerName: "Alan Turing", totalPence: 9900, status: "shipped" };

function serveOrders(byStatus: Record<string, Order[]>) {
  server.use(
    http.get("*/api/orders", ({ request }) => {
      const status = new URL(request.url).searchParams.get("status") ?? "";
      return HttpResponse.json({ data: byStatus[status] ?? [] });
    }),
  );
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <OrdersPage />
    </QueryClientProvider>,
  );
}

test("lists open orders by default", async () => {
  serveOrders({ open: [openOrder] });
  renderPage();

  const table = await screen.findByRole("table", { name: "Orders" });
  const row = within(table).getByRole("row", { name: /ORD-1001/ });
  expect(within(row).getByText("Ada Lovelace")).toBeInTheDocument();
  expect(within(row).getByText("£12.50")).toBeInTheDocument();
});

test("shows the orders for the chosen status", async () => {
  serveOrders({ open: [openOrder], shipped: [shippedOrder] });
  renderPage();
  await screen.findByText("ORD-1001");

  await userEvent.selectOptions(screen.getByRole("combobox", { name: "Status" }), "shipped");

  await screen.findByText("ORD-1002");
  expect(screen.queryByText("ORD-1001")).not.toBeInTheDocument();
});

test("says so when there are no orders with the status", async () => {
  serveOrders({ open: [] });
  renderPage();

  await screen.findByText("No open orders.");
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
});

test("shows an error and reloads when asked", async () => {
  let attempts = 0;
  server.use(
    http.get("*/api/orders", () => {
      attempts += 1;
      return attempts === 1 ? new HttpResponse(null, { status: 500 }) : HttpResponse.json({ data: [openOrder] });
    }),
  );
  renderPage();

  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent("We couldn't load orders.");

  await userEvent.click(within(alert).getByRole("button", { name: "Try again" }));

  await screen.findByText("ORD-1001");
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
TS
