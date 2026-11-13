export type OrderStatus = "open" | "shipped" | "cancelled";

export interface Order {
  id: string;
  number: string;
  customerName: string;
  totalPence: number;
  status: OrderStatus;
}
