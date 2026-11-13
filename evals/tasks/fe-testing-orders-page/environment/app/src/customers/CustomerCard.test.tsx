import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { CustomerCard } from "./CustomerCard";

const queryClient = new QueryClient();

afterEach(() => vi.unstubAllGlobals());

test("shows the customer's name and email", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "c1", name: "Ada Lovelace", email: "ada@example.com" }), { status: 200 }),
    ),
  );

  render(
    <QueryClientProvider client={queryClient}>
      <CustomerCard customerId="c1" />
    </QueryClientProvider>,
  );

  await waitFor(() => expect(screen.getByText("Ada Lovelace")).toBeInTheDocument());
  expect(screen.getByText("ada@example.com")).toBeInTheDocument();
});
