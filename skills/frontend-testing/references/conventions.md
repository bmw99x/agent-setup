# File structure

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
