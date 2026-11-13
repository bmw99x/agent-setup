import { Alert, Button, Select, Stack, TextInput, Textarea } from "@mantine/core";
import { useState } from "react";

import type { RefundReason } from "./types";
import { useRequestRefund } from "./useRequestRefund";

const REASONS: { value: RefundReason; label: string }[] = [
  { value: "damaged", label: "Arrived damaged" },
  { value: "late", label: "Arrived late" },
  { value: "wrong_item", label: "Wrong item" },
];

export function RefundRequestForm({ orderId }: { orderId: string }) {
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState<RefundReason | null>(null);
  const [note, setNote] = useState("");
  const { requestRefund, isRequestingRefund, refundRequested, refundFailed } = useRequestRefund(orderId);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!reason) return;
    const trimmedNote = note.trim();
    requestRefund({
      amountPence: Math.round(Number(amount) * 100),
      reason,
      ...(trimmedNote ? { note: trimmedNote } : {}),
    });
  };

  if (refundRequested) {
    return <Alert title="Refund requested">The customer will be emailed once finance approves it.</Alert>;
  }

  return (
    <form onSubmit={submit}>
      <Stack>
        {refundFailed && (
          <Alert color="red" title="Refund not requested">
            Something went wrong. Check the amount and try again.
          </Alert>
        )}
        <TextInput label="Amount (£)" inputMode="decimal" required value={amount} onChange={(event) => setAmount(event.currentTarget.value)} />
        <Select label="Reason" data={REASONS} required value={reason} onChange={(value) => setReason(value as RefundReason | null)} />
        <Textarea label="Note for finance" value={note} onChange={(event) => setNote(event.currentTarget.value)} />
        <Button type="submit" loading={isRequestingRefund} disabled={!reason || !amount}>
          Request refund
        </Button>
      </Stack>
    </form>
  );
}
