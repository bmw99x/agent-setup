# Async patterns

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
