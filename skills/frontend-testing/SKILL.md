---
name: frontend-testing
description: >
  Use when writing or reviewing frontend tests with Vitest + React Testing Library + MSW.
  Covers RTL query semantics, async patterns, timer handling, MSW v2 setup, React Query
  test config, Mantine-specific stubs, and common anti-patterns.
---

# Frontend Testing

## Core principle

Test observable user-facing behavior, not implementation details. Prefer real hooks + MSW over
mocking data-fetching hooks — MSW lets you test the full data-fetching path while remaining fast
and hermetic.

---

## Vitest config

```ts
// vitest.config.ts / vite.config.ts
test: {
  pool: "forks",        // isolates globals per file; required for MSW + jsdom
  environment: "jsdom",
  setupFiles: "./src/setupTests.ts",
  globals: true,
  css: true,
}
```

`pool: "forks"` is critical with MSW — each file gets its own Node.js process, so global state
(MSW server, `window`, React Query cache) never leaks between files.

---

## setupTests.ts

Global stubs that every file needs. Put them here once — never repeat in individual files.

```ts
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { server } from "./test/msw/server";

// Mantine requires matchMedia and ResizeObserver — jsdom provides neither.
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false, media: query, onchange: null,
    addListener: vi.fn(), removeListener: vi.fn(),
    addEventListener: vi.fn(), removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
class ResizeObserverMock {
  observe() {} unobserve() {} disconnect() {}
}
vi.stubGlobal("ResizeObserver", ResizeObserverMock);

beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

---

## MSW v2

### Server setup

```ts
// src/test/msw/server.ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";
export const server = setupServer(...handlers);
```

### Handlers

```ts
// src/test/msw/handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("*/api/items", () =>
    HttpResponse.json({ data: [{ id: "1", name: "Foo" }] }),
  ),
  http.post("*/api/items", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ data: { id: "new", ...body } }, { status: 201 });
  }),
];
```

### Per-test overrides

```ts
import { server } from "test/msw/server";

it("shows empty state", () => {
  server.use(
    http.get("*/api/items", () =>
      HttpResponse.json({ data: [] }),
    ),
  );
  // server.resetHandlers() in afterEach restores defaults automatically
});
```

### Capturing requests for assertion

```ts
// src/test/msw/captureRequests.ts
import { server } from "./server";

interface CapturedRequest { method: string; url: string; body: unknown }
let captured: CapturedRequest[] = [];

export function clearCapturedRequests() { captured = []; }

export function lastRequest(method: string, urlPattern: RegExp) {
  return [...captured].reverse().find(
    r => r.method === method && urlPattern.test(r.url),
  );
}

export function requestCount(method: string, urlPattern: RegExp) {
  return captured.filter(r => r.method === method && urlPattern.test(r.url)).length;
}

server.events.on("request:start", async ({ request }) => {
  const clone = request.clone();
  let body: unknown;
  try { body = await clone.json(); } catch { body = null; }
  captured.push({ method: request.method, url: request.url, body });
});
```

---

## RTL query semantics

| Query | Use when | Behavior on miss |
|-------|----------|-----------------|
| `getBy*` | Element exists synchronously | throws |
| `findBy*` | Element appears asynchronously | throws after timeout |
| `queryBy*` | Asserting element is absent | returns null |

**Rules:**
- `expect(screen.getByX()).toBeInTheDocument()` — preferred over `toBeTruthy()` (better error msg)
- `await screen.findByText("x")` alone — no `expect().toBeTruthy()` wrapper needed; throw IS the assertion
- `screen.queryBy*` for absence: `expect(screen.queryByText("x")).toBeNull()`
- Replace `waitFor(() => expect(getBy*()).toBeInTheDocument())` with `await findBy*()`

```ts
// ❌ verbose and redundant
await waitFor(() => expect(screen.getByRole("button")).toBeInTheDocument());
expect(await screen.findByText("hello")).toBeTruthy();

// ✅ idiomatic
await screen.findByRole("button");
await screen.findByText("hello");
```

---

## Async patterns

### React Query setup per test

Fresh `QueryClient` per test prevents cache bleed. Always set `retry: false`.

```ts
function renderPage(route = "/") {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <MantineProvider>
      <QueryClientProvider client={queryClient}>
        <MyPage />
      </QueryClientProvider>
    </MantineProvider>,
  );
}
```

### Waiting for MSW data

```ts
it("shows items", async () => {
  render(<ItemList />);
  await screen.findByText("Foo"); // waits for MSW response + React render
});
```

### Asserting HTTP requests were made

```ts
import { lastRequest } from "test/msw/captureRequests";

it("posts correct body", async () => {
  // ... trigger action ...
  await waitFor(() => expect(lastRequest("POST", /\/api\/items$/)).toBeDefined());
  expect(lastRequest("POST", /\/api\/items$/)?.body).toEqual({ name: "Bar" });
});
```

`waitFor` is correct here — `lastRequest` is not a DOM query, so `findBy*` doesn't apply.

---

## Timer handling

**The core conflict:** `waitFor` from RTL uses `setInterval` internally to retry assertions.
`vi.useFakeTimers()` intercepts `setInterval`, so `waitFor` never retries → timeout.

### Rule: hybrid timers for debounce tests

Let MSW data load on real timers, then switch to fake timers only for the synchronous
debounce step:

```ts
it("debounces input before updating URL params", async () => {
  const { history } = renderPage("/items?status=active");

  // 1. Real timers: wait for MSW data to load
  await screen.findByPlaceholderText("Search");

  // 2. Switch to fake timers for the debounce step
  vi.useFakeTimers();
  fireEvent.change(screen.getByPlaceholderText("Search"), {
    target: { value: "foo" },
  });
  expect(new URLSearchParams(history.location.search).get("q")).toBeNull();

  // 3. Advance past debounce window synchronously
  act(() => { vi.advanceTimersByTime(400); });

  expect(new URLSearchParams(history.location.search).get("q")).toBe("foo");
});

afterEach(() => { vi.useRealTimers(); });
```

Never use `vi.useFakeTimers()` in `beforeEach` when the test also needs `waitFor` or `findBy*` — this
will hang. Always restore with `vi.useRealTimers()` in `afterEach`.

### Options that do NOT work

- `vi.useFakeTimers({ shouldAdvanceTime: true })` — unblocks `waitFor` but MSW responses
  arrive asynchronously via real timers; components render empty
- `vi.runAllTimersAsync()` — hangs on polling intervals (infinite timers)

---

## Mantine-specific patterns

### matchMedia + ResizeObserver

Mantine's `@mantine/core` calls `window.matchMedia` on mount and uses `ResizeObserver` for
layout. jsdom provides neither. Stub both in `setupTests.ts` (not per-file — see above).

### modals.openConfirmModal (imperative API)

`@mantine/modals` confirm modals render through a portal and are triggered imperatively.
Capture the config synchronously by mocking the module:

```ts
const openConfirmModalMock = vi.fn();

vi.mock("@mantine/modals", () => ({
  modals: { openConfirmModal: (...args: unknown[]) => openConfirmModalMock(...args) },
}));

afterEach(() => { openConfirmModalMock.mockReset(); });

it("opens confirm with correct title", async () => {
  // ... trigger action ...

  expect(openConfirmModalMock).toHaveBeenCalledTimes(1);

  const config = openConfirmModalMock.mock.calls[0]?.[0] as {
    title: string;
    onConfirm: () => void;
  };
  expect(config.title).toBe("Delete Item");

  // Execute the callback to trigger the mutation
  await act(async () => { config.onConfirm(); });
});
```

### `ModalsProvider` for `useModals` hook

When the component under test uses `useModals()` (not the imperative `modals` object),
wrap the render with `<ModalsProvider>`:

```ts
render(
  <MantineProvider>
    <ModalsProvider>
      <MyComponent />
    </ModalsProvider>
  </MantineProvider>,
);
```

### Selector dropdowns (Mantine `Select`)

Mantine's `Select` renders a hidden combobox — clicking the textbox opens the dropdown:

```ts
fireEvent.click(screen.getByRole("textbox", { name: "Template" }));
// options appear in the document (not inside the textbox)
fireEvent.click(screen.getByText("Option A"));
```

Use `screen.getAllByText(...)` + `.at(-1)` when the same text appears in the field AND the
dropdown list.

### `within()` for dialog scoping

Mantine modals render in a portal. Scope queries to avoid grabbing elements outside:

```ts
const dialog = await screen.findByRole("dialog", { name: "Edit Item" });
const q = within(dialog);
expect(q.getByText("Name")).toBeInTheDocument();
fireEvent.change(q.getByRole("textbox", { name: "Name" }), { target: { value: "New" } });
```

---

## Request body assertions

`idempotencyKey: undefined` in an expected object passes vacuously — JSON serialization drops
`undefined` keys so they are never present in the parsed body:

```ts
// ❌ misleading — idempotencyKey: undefined is always "equal" since JSON drops it
expect(req?.body).toEqual({ name: "x", idempotencyKey: undefined });

// ✅ only assert fields that are actually in the request body
expect(req?.body).toEqual({ name: "x" });
```

---

## React Router v5 + URL param testing

Use `createMemoryHistory` to assert URL state changes without a real browser:

```ts
import { createMemoryHistory } from "history";
import { Router } from "react-router-dom";

function renderPage(route = "/items") {
  const history = createMemoryHistory({ initialEntries: [route] });
  const result = render(
    <Router history={history}>
      <ItemsPage />
    </Router>,
  );
  return { ...result, history };
}

it("updates URL on filter change", async () => {
  const { history } = renderPage("/items?status=active");
  // ...
  expect(new URLSearchParams(history.location.search).get("status")).toBe("sent");
});
```

---

## File structure

```
src/
  setupTests.ts               # global stubs + MSW lifecycle
  test/
    msw/
      server.ts               # setupServer(…handlers)
      handlers.ts             # default handlers
      captureRequests.ts      # lastRequest() / requestCount() helpers
      fixtures/               # shared response fixtures (typed)
```

---

## Anti-patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| `vi.useFakeTimers()` in `beforeEach` | Breaks `waitFor` / `findBy*` | Hybrid: real timers for load, fake for debounce only |
| `expect(await findBy*()).toBeTruthy()` | Redundant — throw is the assertion | Bare `await findBy*()` |
| `waitFor(getBy*().toBeInTheDocument())` | Use findBy* instead | `await findBy*()` |
| `expect(getBy*()).toBeTruthy()` | Weak assertion | `toBeInTheDocument()` |
| `matchMedia` in every `beforeAll` | Duplication | Put in `setupTests.ts` |
| Mocking data-fetching hooks with static data | Skips HTTP layer | Use real hooks + MSW |
| `queryClient` at module scope | Cache bleeding between tests | Create fresh in render helper |
| `undefined` in `toEqual` expected object | JSON drops undefined → vacuously true | Omit undefined keys from expectation |
