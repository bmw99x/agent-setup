import { CommentForm } from "../comments/CommentForm";
import type { Invoice } from "./types";
import { useInvoiceReviewMutations } from "./useInvoiceReviewMutations";

export function InvoiceReview({ invoice }: { invoice: Invoice }) {
  const { approveMutation } = useInvoiceReviewMutations();

  return (
    <section>
      <h2>Invoice {invoice.number}</h2>
      <p>Total: {invoice.total}</p>
      <button type="button" disabled={approveMutation.isPending} onClick={() => approveMutation.mutate(invoice.id)}>
        Approve
      </button>
      <CommentForm invoiceId={invoice.id} />
    </section>
  );
}
