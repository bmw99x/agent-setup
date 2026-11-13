#!/bin/bash
set -euo pipefail
cd /app
mkdir -p src/test/msw
cat > src/test/msw/server.ts <<'TS'
import { setupServer } from "msw/node";

export const server = setupServer();
TS
cat > src/test/msw/captureRequests.ts <<'TS'
import { server } from "./server";

interface CapturedRequest {
  method: string;
  url: string;
  body: unknown;
}

let captured: CapturedRequest[] = [];

server.events.on("request:start", async ({ request }) => {
  const clone = request.clone();
  let body: unknown;
  try {
    body = await clone.json();
  } catch {
    body = null;
  }
  captured.push({ method: request.method, url: request.url, body });
});

export function clearCapturedRequests() {
  captured = [];
}

export function lastRequest(method: string, urlPattern: RegExp) {
  return [...captured].reverse().find((r) => r.method === method && urlPattern.test(r.url));
}
TS
cat > src/setupTests.ts <<'TS'
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll, vi } from "vitest";

import { clearCapturedRequests } from "./test/msw/captureRequests";
import { server } from "./test/msw/server";

// Mantine reads matchMedia and ResizeObserver, which jsdom lacks.
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
vi.stubGlobal("ResizeObserver", ResizeObserverMock);
// Mantine Select scrolls the highlighted option into view; jsdom has no layout.
Element.prototype.scrollIntoView = vi.fn();

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  clearCapturedRequests();
});
afterAll(() => server.close());
TS
cat > src/refunds/RefundRequestForm.test.tsx <<'TS'
import { MantineProvider } from "@mantine/core";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, expect, test } from "vitest";

import { lastRequest } from "../test/msw/captureRequests";
import { server } from "../test/msw/server";
import { RefundRequestForm } from "./RefundRequestForm";

const REFUNDS_URL = /\/api\/orders\/ord-7\/refunds$/;

beforeEach(() => {
  server.use(
    http.post("*/api/orders/:orderId/refunds", async ({ request }) =>
      HttpResponse.json({ id: "ref-1", status: "pending", ...((await request.json()) as object) }, { status: 201 }),
    ),
  );
});

function renderForm() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <MantineProvider>
      <QueryClientProvider client={queryClient}>
        <RefundRequestForm orderId="ord-7" />
      </QueryClientProvider>
    </MantineProvider>,
  );
}

function fillIn({ amount, reason, note }: { amount: string; reason: string; note?: string }) {
  fireEvent.change(screen.getByRole("textbox", { name: /amount/i }), { target: { value: amount } });
  fireEvent.click(screen.getByRole("textbox", { name: /reason/i }));
  fireEvent.click(screen.getByRole("option", { name: reason }));
  if (note !== undefined) {
    fireEvent.change(screen.getByRole("textbox", { name: /note/i }), { target: { value: note } });
  }
  fireEvent.click(screen.getByRole("button", { name: "Request refund" }));
}

test("requests the refund in pence with the reason and note", async () => {
  renderForm();

  fillIn({ amount: "12.50", reason: "Arrived damaged", note: "Box crushed" });

  await screen.findByText("Refund requested");
  expect(lastRequest("POST", REFUNDS_URL)?.body).toEqual({ amountPence: 1250, reason: "damaged", note: "Box crushed" });
});

test("leaves the note out when none was typed", async () => {
  renderForm();

  fillIn({ amount: "3", reason: "Wrong item", note: "   " });

  await screen.findByText("Refund requested");
  expect(lastRequest("POST", REFUNDS_URL)?.body).toEqual({ amountPence: 300, reason: "wrong_item" });
});

test("keeps the form and shows an error when the API refuses", async () => {
  server.use(http.post("*/api/orders/:orderId/refunds", () => HttpResponse.json({ detail: "too much" }, { status: 422 })));
  renderForm();

  fillIn({ amount: "999", reason: "Arrived late" });

  await screen.findByText("Refund not requested");
  expect(screen.getByRole("button", { name: "Request refund" })).toBeInTheDocument();
  expect(screen.queryByText("Refund requested")).not.toBeInTheDocument();
  await waitFor(() => expect(lastRequest("POST", REFUNDS_URL)).toBeDefined());
});
TS
