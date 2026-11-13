# Order summary is broken in dark mode

People using dark mode see the checkout's order summary (`src/orders/OrderSummary.tsx`) as a bright white box, and the "Prices include VAT." note is hard to read. The app follows the operating system's colour scheme (`defaultColorScheme="auto"` in `src/main.tsx`), and everything else already switches correctly.

Make the order summary look right in both light and dark mode. In light mode it should look the same as it does today.

Keep `npm test` and `npm run typecheck` passing.
