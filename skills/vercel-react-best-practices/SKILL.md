---
name: vercel-react-best-practices
description: React performance optimization guidelines from Vercel Engineering. Use when writing, reviewing, or refactoring React components. Triggers on tasks involving React components, data fetching, bundle optimization, re-render issues, or performance improvements.
---

# React Best Practices

Vercel Engineering, v1.0.0 (January 2026). Scoped to **React SPAs** (Vite, CRA) — SSR, streaming, Next.js, and React 19 experimental rules have been removed.

51 rules across 7 areas. Each area lives in a reference file with full explanations and incorrect/correct examples. **Read only the file covering the problem in front of you** — the rules are independent, and loading all of them costs far more than it helps.

Roughly ordered by real-world impact: waterfalls and bundle size dominate; JavaScript micro-optimizations rarely matter unless a profile says otherwise.

## Which file to read

| Read | When the problem is | Rules |
| --- | --- | --- |
| `references/waterfalls.md` | Sequential awaits, requests that should overlap, slow initial load | 1.1–1.5 |
| `references/bundle-size.md` | Large bundles, barrel imports, code that should be lazy | 2.1–2.6 |
| `references/data-fetching.md` | Duplicate requests, event listeners, SWR, localStorage | 4.1–4.4 |
| `references/re-renders.md` | Components re-rendering too often; memo, effect, and state shape | 5.1–5.15 |
| `references/rendering-performance.md` | Paint and layout cost — long lists, SVG, static JSX, script tags | 6.1–6.11 |
| `references/javascript-performance.md` | Hot loops, repeated lookups, array passes, layout thrashing | 7.1–7.14 |
| `references/advanced-patterns.md` | App-level init running per mount, handlers in refs | 8.2–8.3 |

## Rule index

Match the symptom here, then open that area's file.

**Waterfalls** — check cheap conditions before async flags · defer await until needed · dependency-based parallelization · `Promise.all()` for independent operations

**Bundle size** — avoid barrel file imports · conditional module loading · dynamic imports for heavy components · prefer statically analyzable paths · preload on user intent

**Data fetching** — deduplicate global event listeners · passive listeners for scrolling · SWR for automatic deduplication · version and minimize localStorage

**Re-renders** — derive state during render · defer state reads to usage point · don't `useMemo` a primitive expression · don't define components inside components · hoist default non-primitive props · extract to memoized components · narrow effect dependencies · put interaction logic in event handlers · split combined hook computations · subscribe to derived state · functional `setState` · lazy state init · transitions for non-urgent updates · `useDeferredValue` for expensive derived renders · `useRef` for transient values

**Rendering** — animate the SVG wrapper not the element · `content-visibility` for long lists · hoist static JSX · optimize SVG precision · `defer`/`async` on script tags · explicit conditional rendering · `useTransition` over manual loading states

**JavaScript** — avoid layout thrashing · index maps for repeated lookups · cache property access in loops · cache repeated calls · cache storage API calls · combine array iterations · `requestIdleCallback` for non-critical work · early length check · early return · hoist RegExp · `flatMap` to map+filter in one pass · loop for min/max over sort · `Set`/`Map` for O(1) lookups · `toSorted()` for immutability

**Advanced** — initialize app once not per mount · store event handlers in refs

## References

1. [react.dev](https://react.dev)
2. [nextjs.org](https://nextjs.org)
3. [swr.vercel.app](https://swr.vercel.app)
4. [better-all](https://github.com/shuding/better-all)
5. [node-lru-cache](https://github.com/isaacs/node-lru-cache)
6. [How we optimized package imports in Next.js](https://vercel.com/blog/how-we-optimized-package-imports-in-next-js)
7. [How we made the Vercel dashboard twice as fast](https://vercel.com/blog/how-we-made-the-vercel-dashboard-twice-as-fast)
