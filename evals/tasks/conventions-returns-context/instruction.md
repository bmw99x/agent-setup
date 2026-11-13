# Customer returns

Customers can ask to send back an order. Add returns to the API in `/app`:

- `POST /returns` with `order_id` and `reason` opens a return for an existing order (404 if the order doesn't exist). A new return starts in status `requested`. Respond 201 with the return's `id`, `order_id`, `reason` and `status`.
- `GET /returns/{return_id}` returns one return, or 404.
- `POST /returns/{return_id}/approve` and `POST /returns/{return_id}/reject` move a `requested` return to `approved` or `rejected`. Deciding a return that is not `requested` any more is a 409.

Only staff may use the returns endpoints, same as orders. Store returns in the database like orders, and keep the tests in `/app/tests` passing.
