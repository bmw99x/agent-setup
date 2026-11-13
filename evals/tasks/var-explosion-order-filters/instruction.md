# Make order filters cheap to extend

Every time product asks for a new filter on the orders listing we end up editing three method signatures in `/app/orders/service.py`, three copies of the same filter-building code, and every call in `/app/orders/api.py`. A `currency` filter and a `created_after` filter are already on the roadmap.

Refactor the order filtering so that the next filter is a small change. Don't add the new filters yet.

The handlers in `orders/api.py` are the public interface and must behave exactly as they do today; `/app/tests` must still pass.
