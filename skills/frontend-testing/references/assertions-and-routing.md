# Request body assertions

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
