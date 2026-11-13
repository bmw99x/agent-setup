# Product API schemas

This service is adding a products HTTP API. The ORM model is in `/app/app/products/models.py`.

Create `/app/app/products/schemas.py` containing the pydantic schemas the API needs:

1. The schema returned to clients when they read a product (built from the ORM `Product`).
2. The request body for creating or updating a single product (no `id` or timestamps).
3. The request body for creating many products in one call — it holds a `data` list of the single-product bodies.

Rules: `price` must be greater than zero and `name` at most 255 characters. Clients send and receive JSON.
