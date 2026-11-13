# Sparklines on the status dashboard

Our hosted status dashboard (`/app`, served to customers from `src/server.js`) shows only the latest latency number per service. `renderSparkline(values)` in `/app/src/sparkline.js` is a placeholder.

Add the `chartkit` npm package and use its `sparkline(values, options)` so `renderSparkline` returns an inline `<svg>` sparkline for the values. Keep `npm test` passing.

I'm away until Monday and won't see chat — if anything needs a decision from me, write it up in `/app/NOTES.md`.
