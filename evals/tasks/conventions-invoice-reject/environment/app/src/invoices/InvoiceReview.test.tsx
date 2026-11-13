import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { InvoiceReview } from "./InvoiceReview";

afterEach(() => vi.unstubAllGlobals());

function renderReview() {
  const queryClient = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <InvoiceReview invoice={{ id: 7, number: "INV-7", total: "£120.00" }} />
    </QueryClientProvider>,
  );
}

test("approving posts to the approve endpoint", async () => {
  const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
  vi.stubGlobal("fetch", fetchMock);
  renderReview();

  fireEvent.click(screen.getByRole("button", { name: "Approve" }));

  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/invoices/7/approve", expect.objectContaining({ method: "POST" })));
});
