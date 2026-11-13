# Shipping quotes

Checkout needs to charge for shipping. `CheckoutService.shipping_cost` in `/app/app/checkout/service.py` is a stub.

Implement the shipping price calculation in the `app/shipping` package (create whatever modules you need) and wire `CheckoutService.shipping_cost` to it. `app/shipping` must not import anything from `app/checkout`: checkout depends on shipping, not the other way round. Other services will reuse shipping quotes later.

Pricing rules (all amounts GBP):

- We only ship from our UK warehouse, so the origin country must be `GB`.
- Destinations we serve and their base rate: `GB` 4.50, `IE` 6.00, `FR` 7.50, `DE` 7.50.
- Chargeable weight is the larger of the actual weight in kg and the volumetric weight (length x width x height in cm, divided by 5000).
- Price is the base rate plus 1.20 for every chargeable kg above the first kg (a fraction of a kg is charged pro rata).
- Express delivery doubles the price.
- Round the final price to 2 decimal places, half up.

An order with an unsupported origin or destination must be rejected with an error the API layer can turn into a 4xx response.
