# MSW v2

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
