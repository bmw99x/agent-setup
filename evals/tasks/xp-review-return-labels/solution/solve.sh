#!/bin/bash
set -e
cat > /app/REVIEW.md <<'MD'
# Review: feature/customer-returns

Solves the right problem and the tests cover both new paths.

## Consider

- `app/shipping/labels.py:8-28` `render_label` now takes `is_return` and branches on it in four places (addressee, header, barcode, routing, footer). That is two labels wearing similar clothes: a wrong abstraction. Inline it back into a `render_outbound_label` and a `render_return_label` that each own their differences; share only what is genuinely common.
- `app/shipping/notifications.py:17-22` `return_instructions` copies the address-block formatting that already lives in `labels.py` and `manifest.py`. This is the third copy, so extract it now: `format_address(address) -> list[str]`, and use it from all three.

## Done well

The weight total in `returns.py` repeats `labels.py` once; fine for now, wait for a third use before extracting it.
MD
