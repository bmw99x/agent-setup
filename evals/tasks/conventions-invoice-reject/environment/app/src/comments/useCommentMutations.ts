import { useMutation, useQueryClient } from "@tanstack/react-query";

import { postJson } from "../api";

export function useCommentMutations(invoiceId: number) {
  const queryClient = useQueryClient();

  const addCommentMutation = useMutation({
    mutationFn: (text: string) => postJson(`/api/invoices/${invoiceId}/comments`, { text }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["invoices", invoiceId, "comments"] }),
  });

  return { addCommentMutation };
}
