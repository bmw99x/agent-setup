import type { Invite } from "./types";

export async function inviteMember(invite: Invite): Promise<void> {
  const response = await fetch("/api/team/invites", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(invite),
  });
  if (!response.ok) throw new Error(`Invite failed: ${response.status}`);
}
