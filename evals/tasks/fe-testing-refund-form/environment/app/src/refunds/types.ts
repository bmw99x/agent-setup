export type RefundReason = "damaged" | "late" | "wrong_item";

export interface RefundRequest {
  amountPence: number;
  reason: RefundReason;
  note?: string;
}

export interface Refund extends RefundRequest {
  id: string;
  status: "pending";
}
