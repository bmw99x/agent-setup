# Session export: quote latency (copied from the other terminal)

**User:** The storefront's quote endpoint is too slow. I need quote lookups under 50 ms p95 without making the pricing team run a new database. Let's explore options.

**Claude:** Let me measure the current endpoint first.

**Tool result (bench/quote_bench.py, staging-2, fixture `skus_120k`, 120,000 SKUs, 10k requests):**
```
uncached GET /quotes/{sku}: p50 141 ms, p95 212 ms
```

**Claude:** 212 ms p95 against a 50 ms target. Options: Redis read-through cache, Memcached, a Postgres materialised view, or CDN edge caching.

**Claude:** Materialised views won't work here: refreshing one every minute takes a lock on the table and will stall writes from the pricing team's batch job. I'd rule that out.

**User:** No to Memcached. Ops won't take on another stateful service this year, and we already run Redis for sessions.

**Claude:** Prototyping a Redis read-through cache on the existing sessions cluster.

**Tool result (bench/quote_bench.py, staging-2, fixture `skus_120k`, Redis read-through, warm cache, 10k requests):**
```
cached GET /quotes/{sku}: p50 2.1 ms, p95 6.8 ms, hit rate 97.4%
```

**User:** Nice. What about the CDN edge-cache idea?

**Claude:** It would need cache-key changes in the storefront and a purge hook on price updates.

**User:** Let's park CDN edge caching until after the Q1 change freeze; the storefront team can't touch cache keys before then.

**Claude:** Understood. Redis is clearly the way to go; next step is to wire it into `pricing/quote_service.py` with a 60 s TTL.

**User:** Hmm. We never even looked at precomputing quotes nightly into a flat table. Anyway, the session's got long and I don't want the next one just rubber-stamping Redis.
