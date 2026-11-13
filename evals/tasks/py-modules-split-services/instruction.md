# Break up the billing services module

`/app/app/services.py` holds the customer, order and invoice logic for our billing service and has become painful to review — every MR touches it and the diffs are hard to follow.

Restructure it so the code is easier to find and review. Behaviour must not change, and the test suite in `/app/tests` must stay green (update its imports if you move things).
