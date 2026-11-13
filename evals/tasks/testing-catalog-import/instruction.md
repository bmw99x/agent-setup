# Tests for the supplier feed import

`CatalogImporter.import_rows` in `/app/app/catalog/importer.py` loads supplier product feeds into our catalog. Last week a feed with the same SKU listed twice (once as `ab-100`, once as `AB-100 `) caused a mess, and there are no tests for the importer.

Write unit tests for it under `/app/tests/`, including duplicate handling. They have to run in CI, which has no network, and downloading supplier images is slow and metered. `pytest` from `/app` should pass.
