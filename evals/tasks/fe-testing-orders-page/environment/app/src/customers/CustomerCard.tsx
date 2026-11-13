import { useCustomer } from "./useCustomer";

export function CustomerCard({ customerId }: { customerId: string }) {
  const customer = useCustomer(customerId);

  if (customer.isPending) return <p>Loading customer…</p>;
  if (customer.isError) return <p>Customer unavailable.</p>;

  return (
    <article aria-label="Customer">
      <h2>{customer.data.name}</h2>
      <a href={`mailto:${customer.data.email}`}>{customer.data.email}</a>
    </article>
  );
}
