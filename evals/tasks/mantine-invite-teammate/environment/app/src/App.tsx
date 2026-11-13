import { Container } from "@mantine/core";

import { TeamPage } from "./team/TeamPage";

const members = [
  { id: "1", name: "Ada Lovelace", email: "ada@acme.test", role: "admin" as const },
  { id: "2", name: "Grace Hopper", email: "grace@acme.test", role: "member" as const },
];

export function App() {
  return (
    <Container size="lg" py="xl">
      <TeamPage members={members} />
    </Container>
  );
}
