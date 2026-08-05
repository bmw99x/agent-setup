# Vitest config

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
