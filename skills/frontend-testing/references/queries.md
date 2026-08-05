# RTL query semantics

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
