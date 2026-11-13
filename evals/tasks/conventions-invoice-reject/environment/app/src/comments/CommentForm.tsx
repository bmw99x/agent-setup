import { useState } from "react";

import { useCommentMutations } from "./useCommentMutations";

export function CommentForm({ invoiceId }: { invoiceId: number }) {
  const [text, setText] = useState("");
  const { addCommentMutation } = useCommentMutations(invoiceId);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    addCommentMutation.mutate(text, { onSuccess: () => setText("") });
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Comment
        <input value={text} onChange={(event) => setText(event.target.value)} />
      </label>
      <button type="submit" disabled={addCommentMutation.isPending}>
        Add comment
      </button>
    </form>
  );
}
