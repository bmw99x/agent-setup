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

let captured: URL[] = [];

server.events.on("request:start", ({ request }) => {
  captured.push(new URL(request.url));
});

export function clearCapturedRequests() {
  captured = [];
}

export function searchTermsRequested() {
  return captured.filter((url) => url.pathname === "/api/products").map((url) => url.searchParams.get("q"));
}
TS
cat > src/setupTests.ts <<'TS'
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll, vi } from "vitest";

import { clearCapturedRequests } from "./test/msw/captureRequests";
import { server } from "./test/msw/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  vi.useRealTimers();
  server.resetHandlers();
  clearCapturedRequests();
});
afterAll(() => server.close());
TS
cat > src/products/ProductSearch.test.tsx <<'TS'
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, expect, test, vi } from "vitest";

import { searchTermsRequested } from "../test/msw/captureRequests";
import { server } from "../test/msw/server";
import { ProductSearch, SEARCH_DELAY_MS } from "./ProductSearch";
import type { Product } from "./types";

const popular: Product[] = [{ id: "p1", name: "Desk lamp", sku: "LMP-1" }];
const catalogue: Product[] = [
  { id: "p2", name: "Oak table", sku: "TBL-1" },
  { id: "p3", name: "Oak chair", sku: "CHR-1" },
];

beforeEach(() => {
  server.use(
    http.get("*/api/products", ({ request }) => {
      const q = new URL(request.url).searchParams.get("q");
      if (q === null) return HttpResponse.json({ data: popular });
      return HttpResponse.json({ data: catalogue.filter((p) => p.name.toLowerCase().includes(q.toLowerCase())) });
    }),
  );
});

function renderSearch() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ProductSearch />
    </QueryClientProvider>,
  );
}

function typeInto(input: HTMLElement, text: string) {
  for (let i = 1; i <= text.length; i += 1) {
    fireEvent.change(input, { target: { value: text.slice(0, i) } });
  }
}

test("shows popular products before searching", async () => {
  renderSearch();

  await screen.findByText("Desk lamp");
  expect(screen.getByRole("heading", { name: "Popular products" })).toBeInTheDocument();
});

test("searches once typing pauses, with the final term only", async () => {
  renderSearch();
  const input = await screen.findByRole("searchbox", { name: "Search products" });
  await screen.findByText("Desk lamp");

  vi.useFakeTimers();
  typeInto(input, "oak");
  act(() => vi.advanceTimersByTime(SEARCH_DELAY_MS - 1));
  expect(screen.getByRole("heading", { name: "Popular products" })).toBeInTheDocument();
  act(() => vi.advanceTimersByTime(1));
  vi.useRealTimers();

  await screen.findByText("Oak table");
  expect(screen.getByText("Oak chair")).toBeInTheDocument();
  expect(searchTermsRequested()).toEqual([null, "oak"]);
});

test("does not search for a single character", async () => {
  renderSearch();
  const input = await screen.findByRole("searchbox", { name: "Search products" });
  await screen.findByText("Desk lamp");

  vi.useFakeTimers();
  typeInto(input, "o");
  act(() => vi.advanceTimersByTime(SEARCH_DELAY_MS * 2));
  vi.useRealTimers();

  expect(screen.getByRole("heading", { name: "Popular products" })).toBeInTheDocument();
  expect(searchTermsRequested()).toEqual([null]);
});

test("says when nothing matches", async () => {
  renderSearch();
  const input = await screen.findByRole("searchbox", { name: "Search products" });

  fireEvent.change(input, { target: { value: "sofa" } });

  await screen.findByText("No products match “sofa”.");
});
TS
