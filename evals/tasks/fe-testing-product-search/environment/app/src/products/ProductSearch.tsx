import { useState } from "react";

import { useDebouncedValue } from "./useDebouncedValue";
import { useProducts } from "./useProducts";

export const SEARCH_DELAY_MS = 300;
const MIN_SEARCH_LENGTH = 2;

export function ProductSearch() {
  const [input, setInput] = useState("");
  const debouncedInput = useDebouncedValue(input.trim(), SEARCH_DELAY_MS);
  const searchTerm = debouncedInput.length >= MIN_SEARCH_LENGTH ? debouncedInput : "";
  const products = useProducts(searchTerm);

  return (
    <section>
      <label>
        Search products
        <input type="search" value={input} onChange={(event) => setInput(event.target.value)} />
      </label>

      <h2>{searchTerm ? `Results for “${searchTerm}”` : "Popular products"}</h2>

      {products.isPending && <p>Loading…</p>}
      {products.isError && <p role="alert">Search is unavailable right now.</p>}
      {products.isSuccess && products.data.length === 0 && <p>No products match “{searchTerm}”.</p>}
      {products.isSuccess && products.data.length > 0 && (
        <ul aria-label="Products">
          {products.data.map((product) => (
            <li key={product.id}>
              {product.name} <small>{product.sku}</small>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
