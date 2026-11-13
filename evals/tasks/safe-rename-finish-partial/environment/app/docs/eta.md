# How the delivery ETA is computed

`est_delivery` counts working days forward from the dispatch date, skipping Saturdays and
Sundays: standard is 3 working days, express is 1. Bank holidays are not handled yet.

`latest_delivery` adds the service buffer (2 working days standard, 1 express) on top of
`est_delivery`; that is the date in the customer's confirmation email.
