import { useQuery } from "@tanstack/react-query";

import { getJson } from "../api/client";

export interface Customer {
  id: string;
  name: string;
  email: string;
}

export function useCustomer(customerId: string) {
  return useQuery({
    queryKey: ["customers", customerId],
    queryFn: () => getJson<Customer>(`/api/customers/${customerId}`),
  });
}
