import { useQuery } from "@tanstack/react-query";

import { getJson } from "../api/client";
import type { Product } from "./types";

export function useProducts(searchTerm: string) {
  return useQuery({
    queryKey: ["products", searchTerm],
    queryFn: async () => {
      const query = searchTerm ? `?q=${encodeURIComponent(searchTerm)}` : "";
      const page = await getJson<{ data: Product[] }>(`/api/products${query}`);
      return page.data;
    },
  });
}
