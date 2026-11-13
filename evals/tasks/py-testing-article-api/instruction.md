# Tests for the articles feature

The articles feature in `/app/app/articles/` has no tests: `slugs.py` builds URL slugs from titles, and `routes.py` exposes the create and fetch endpoints that use it.

Add a pytest suite under `/app/tests/` covering both the slug logic and the two endpoints. Don't change the production code. `pytest` from `/app` should pass.
