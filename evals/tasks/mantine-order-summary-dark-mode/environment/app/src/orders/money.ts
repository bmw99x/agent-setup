const formatter = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" });

export function formatMoney(pence: number) {
  return formatter.format(pence / 100);
}
