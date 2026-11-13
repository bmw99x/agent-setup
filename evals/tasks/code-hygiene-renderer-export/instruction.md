# Export a report as PDF

We have a small reports API (FastAPI, in `/app`). Add an endpoint `POST /reports/{report_id}/export` that returns the report as a PDF (`application/pdf`).

PDFs come from our internal renderer service. It takes `POST /render` with a JSON body `{"title": ..., "rows": [...]}` and responds with the PDF bytes. In dev the renderer runs at `http://renderer.internal:8080`; staging and prod each have their own host. Big reports can take up to 60 seconds to render.

Unknown report → 404. If the renderer is down or errors, the client should get a 503.
