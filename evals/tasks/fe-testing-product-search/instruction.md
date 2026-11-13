# Tests for product search

`/app/src/products/ProductSearch.tsx` is the product search box in the shop admin. It has no tests. Add some.

How it should behave:

- Before anything is typed it shows the popular products.
- It searches as the user types, but only once they pause for 300 ms, so a burst of keystrokes sends one search for the final text, not one per key.
- Terms shorter than 2 characters don't search; the popular products stay.
- When nothing matches it says so.

CI has no access to the products API. Don't change the component or its hooks. `npm test` must pass.
