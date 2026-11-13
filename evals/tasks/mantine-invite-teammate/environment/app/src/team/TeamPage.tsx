import { Badge, Button, Table } from "@mantine/core";

import { PageHeader } from "../layout/PageHeader";
import type { Member } from "./types";

export function TeamPage({ members }: { members: Member[] }) {
  return (
    <>
      <PageHeader title="Team" subtitle={`${members.length} members`} actions={<Button>Invite teammate</Button>} />
      <Table striped>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Name</Table.Th>
            <Table.Th>Email</Table.Th>
            <Table.Th>Role</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {members.map((member) => (
            <Table.Tr key={member.id}>
              <Table.Td>{member.name}</Table.Td>
              <Table.Td>{member.email}</Table.Td>
              <Table.Td>
                <Badge variant="light" color={member.role === "admin" ? "grape" : "gray"}>
                  {member.role}
                </Badge>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </>
  );
}
