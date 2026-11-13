#!/bin/bash
set -euo pipefail
cd /app
cat > src/invoices/useInvoiceReviewMutations.ts <<'TS'
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { postJson } from "../api";

export function useInvoiceReviewMutations() {
  const queryClient = useQueryClient();
  const refreshInvoices = () => queryClient.invalidateQueries({ queryKey: ["invoices"] });

  const approveMutation = useMutation({
    mutationFn: (invoiceId: number) => postJson(`/api/invoices/${invoiceId}/approve`),
    onSuccess: refreshInvoices,
  });
  const rejectMutation = useMutation({
    mutationFn: (invoiceId: number) => postJson(`/api/invoices/${invoiceId}/reject`),
    onSuccess: refreshInvoices,
  });

  return {
    approve: (invoiceId: number) => approveMutation.mutate(invoiceId),
    reject: (invoiceId: number) => rejectMutation.mutate(invoiceId),
    isApproving: approveMutation.isPending,
    isRejecting: rejectMutation.isPending,
  };
}
TS
cat > src/invoices/InvoiceReview.tsx <<'TS'
import { CommentForm } from "../comments/CommentForm";
import type { Invoice } from "./types";
import { useInvoiceReviewMutations } from "./useInvoiceReviewMutations";

export function InvoiceReview({ invoice }: { invoice: Invoice }) {
  const { approve, reject, isApproving, isRejecting } = useInvoiceReviewMutations();
  const isDeciding = isApproving || isRejecting;

  return (
    <section>
      <h2>Invoice {invoice.number}</h2>
      <p>Total: {invoice.total}</p>
      <button type="button" disabled={isDeciding} onClick={() => approve(invoice.id)}>
        Approve
      </button>
      <button type="button" disabled={isDeciding} onClick={() => reject(invoice.id)}>
        Reject
      </button>
      <CommentForm invoiceId={invoice.id} />
    </section>
  );
}
TS
cat > src/comments/useCommentMutations.ts <<'TS'
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { postJson } from "../api";

export function useCommentMutations(invoiceId: number) {
  const queryClient = useQueryClient();

  const addCommentMutation = useMutation({
    mutationFn: (text: string) => postJson(`/api/invoices/${invoiceId}/comments`, { text }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["invoices", invoiceId, "comments"] }),
  });

  return {
    addComment: (text: string, onAdded?: () => void) => addCommentMutation.mutate(text, { onSuccess: onAdded }),
    isAddingComment: addCommentMutation.isPending,
  };
}
TS
cat > src/comments/CommentForm.tsx <<'TS'
import { useState } from "react";

import { useCommentMutations } from "./useCommentMutations";

export function CommentForm({ invoiceId }: { invoiceId: number }) {
  const [text, setText] = useState("");
  const { addComment, isAddingComment } = useCommentMutations(invoiceId);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    addComment(text, () => setText(""));
  };

  return (
    <form onSubmit={submit}>
      <label>
        Comment
        <input value={text} onChange={(event) => setText(event.target.value)} />
      </label>
      <button type="submit" disabled={isAddingComment}>
        Add comment
      </button>
    </form>
  );
}
TS
