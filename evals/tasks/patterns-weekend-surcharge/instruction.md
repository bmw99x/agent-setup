# Weekend delivery surcharge

From next month deliveries scheduled for a Saturday or Sunday cost £2.00 more. Orders that qualify for free delivery stay free at weekends.

Delivery fees are calculated in `/app/app/delivery/fees.py` (`delivery_fee`), and checkout uses it. Please add the surcharge and cover it with tests in `/app/tests/`.

For context: marketing have mentioned peak-hour and bank-holiday surcharges as ideas for later in the year, but nothing about them is decided.
