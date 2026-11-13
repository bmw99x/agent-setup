# Pull loyalty into its own package

The loyalty-points code in `/app` is spread across `app/domain/`, `app/repositories/`, `app/services/` and `app/subscribers/`, which makes it hard for the loyalty team to own. Move everything loyalty-related into a new `app/loyalty/` package so they have one place to work in. This is a pure reorganisation: no behaviour change.

Tests run with `python -m pytest` from `/app`.
