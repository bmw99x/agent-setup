import { useMutation } from "@tanstack/react-query";

import { postJson } from "../api/client";
import type { Refund, RefundRequest } from "./types";

export function useRequestRefund(orderId: string) {
  const mutation = useMutation({
    mutationFn: (request: RefundRequest) => postJson<Refund>(`/api/orders/${orderId}/refunds`, request),
  });

  return {
    requestRefund: mutation.mutate,
    isRequestingRefund: mutation.isPending,
    refundRequested: mutation.isSuccess,
    refundFailed: mutation.isError,
  };
}
