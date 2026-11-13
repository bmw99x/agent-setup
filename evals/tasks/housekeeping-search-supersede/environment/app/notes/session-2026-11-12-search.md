# Session export: search, round two (copied from the other terminal)

**User:** Read the October brief in `.claude/housekeeping/` and let's keep going on typo-tolerant search.

**Claude:** Read it. Trying the pg_trgm index it lists as untested.

**Tool result (scripts/bench_search.py, staging, full catalogue 400k products, 2,000-query typo set):**
```
pg_trgm GIN, similarity >= 0.3: p95 38 ms, typo recall 81%
```

**Claude:** Elasticsearch would give fuzzy matching and better ranking out of the box.

**User:** No Elasticsearch. Not because of any number — I just don't want to babysit a JVM cluster.

**Claude:** Typesense handles typos much better than pg_trgm and would push recall above 95%.

**User:** I ran the load test against my laptop build last night with the trigram index: 180 req/s before it fell over.

**Claude:** That's well above the ~30 searches/s peak.

**User:** What about learning-to-rank?

**Claude:** It needs labelled click data.

**User:** Park learning-to-rank — we have no labelled data until the March click-log export lands.

**Claude:** Agreed. pg_trgm is the best option here; next step is a migration adding the GIN index.

**User:** Let's stop here. Same as last time, I want a clean session to take over.
