import { useQuery } from "@tanstack/react-query";

import { getJson } from "../api/client";
import type { Order, OrderStatus } from "./types";

export function useOrders(status: OrderStatus) {
  return useQuery({
    queryKey: ["orders", status],
    queryFn: async () => {
      const page = await getJson<{ data: Order[] }>(`/api/orders?status=${status}`);
      return page.data;
    },
  });
}
