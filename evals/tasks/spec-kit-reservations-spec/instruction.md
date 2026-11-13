# Reservations

Members keep asking the desk to hold books that are out on loan. We use spec-kit in this repo (`/app`). Let's get the reservations feature going:

- A member can reserve a book that is currently on loan. Several members can queue for the same book; first come, first served.
- When the book comes back it is held for the first member in the queue for a few days, and nobody else can borrow it meanwhile. That member is told it is ready to collect.
- If they don't collect it in time, the hold passes to the next member in the queue.
- A member can cancel their reservation.

I'm away for the rest of the day; leave anything for me in `/app/HANDOFF.md`.
