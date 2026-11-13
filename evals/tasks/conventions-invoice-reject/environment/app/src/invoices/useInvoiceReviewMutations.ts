import { useMutation, useQueryClient } from "@tanstack/react-query";

import { postJson } from "../api";

export function useInvoiceReviewMutations() {
  const queryClient = useQueryClient();

  const approveMutation = useMutation({
    mutationFn: (invoiceId: number) => postJson(`/api/invoices/${invoiceId}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["invoices"] }),
  });

  return { approveMutation };
}
