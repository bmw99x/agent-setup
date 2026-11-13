import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, expect, test, vi } from "vitest";

import * as commentHooks from "../comments/useCommentMutations";
import { InvoiceReview } from "../invoices/InvoiceReview";
import * as invoiceHooks from "../invoices/useInvoiceReviewMutations";

afterEach(() => vi.unstubAllGlobals());

function deferredFetch() {
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const fetchMock = vi.fn(async () => {
    await gate;
    return new Response("{}", { status: 200 });
  });
  vi.stubGlobal("fetch", fetchMock);
  return { fetchMock, release };
}

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

function looksLikeMutationObject(value: unknown) {
  return typeof value === "object" && value !== null && "mutate" in value && "isPending" in value;
}

function assertDomainShape(api: Record<string, unknown>) {
  for (const [key, value] of Object.entries(api)) {
    expect(key, `hook exposes ${key}`).not.toMatch(/Mutation$/);
    expect(key, `hook exposes ${key}`).not.toMatch(/^handle[A-Z]/);
    expect(looksLikeMutationObject(value), `${key} is a raw mutation object`).toBe(false);
  }
}

function keyMatching(api: Record<string, unknown>, pattern: RegExp, type: string) {
  const key = Object.keys(api).find((k) => pattern.test(k) && typeof api[k] === type);
  expect(key, `no ${type} matching ${pattern} in ${Object.keys(api).join(", ")}`).toBeDefined();
  return key as string;
}

function useInvoiceHook() {
  const hook = (invoiceHooks as Record<string, unknown>).useInvoiceReviewMutations as (id: number) => Record<string, unknown>;
  return renderHook(() => hook(42), { wrapper });
}

test("reject button: posts to reject endpoint, both buttons disabled while pending", async () => {
  const { fetchMock, release } = deferredFetch();
  render(<InvoiceReview invoice={{ id: 42, number: "INV-42", total: "£10.00" }} />, { wrapper });

  fireEvent.click(screen.getByRole("button", { name: /reject/i }));

  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith("/api/invoices/42/reject", expect.objectContaining({ method: "POST" })),
  );
  await waitFor(() => expect((screen.getByRole("button", { name: /reject/i }) as HTMLButtonElement).disabled).toBe(true));
  expect((screen.getByRole("button", { name: /approve/i }) as HTMLButtonElement).disabled).toBe(true);
  release();
  await waitFor(() => expect((screen.getByRole("button", { name: /approve/i }) as HTMLButtonElement).disabled).toBe(false));
});

test("invoice hook exposes domain verbs and is-ing flags, not mutation objects", () => {
  deferredFetch();
  const { result } = useInvoiceHook();
  assertDomainShape(result.current);
  keyMatching(result.current, /^approve/, "function");
  keyMatching(result.current, /^reject/, "function");
  keyMatching(result.current, /^isApproving/, "boolean");
  keyMatching(result.current, /^isRejecting/, "boolean");
});

test("reject verb drives the isRejecting flag", async () => {
  const { fetchMock, release } = deferredFetch();
  const { result } = useInvoiceHook();
  const verb = keyMatching(result.current, /^reject/, "function");
  const flag = keyMatching(result.current, /^isRejecting/, "boolean");

  act(() => {
    (result.current[verb] as (id: number) => void)(42);
  });

  await waitFor(() => expect(result.current[flag]).toBe(true));
  expect(fetchMock).toHaveBeenCalledWith("/api/invoices/42/reject", expect.objectContaining({ method: "POST" }));
  release();
  await waitFor(() => expect(result.current[flag]).toBe(false));
});

test("comment hook also exposes domain verbs and is-ing flags", () => {
  deferredFetch();
  const hook = (commentHooks as Record<string, unknown>).useCommentMutations as (id: number) => Record<string, unknown>;
  const { result } = renderHook(() => hook(42), { wrapper });
  assertDomainShape(result.current);
  keyMatching(result.current, /^[a-z]+[A-Za-z]*$/, "function");
  keyMatching(result.current, /^is[A-Z][A-Za-z]*ing/, "boolean");
});
