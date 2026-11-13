export type Role = "member" | "admin";

export type Member = { id: string; name: string; email: string; role: Role };

export type Invite = { email: string; role: Role };
