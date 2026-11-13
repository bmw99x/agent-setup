type Quote = { subtotal: string; vat: string; total: string };

export function OrderSummary({ quote }: { quote?: Quote }) {
  return (
    <dl>
      <dt>Total</dt>
      <dd>{quote?.total ?? "—"}</dd>
    </dl>
  );
}
