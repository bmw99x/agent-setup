#!/bin/bash
set -euo pipefail
cd /app
cat > src/team/InviteMemberModal.tsx <<'TSX'
import { Button, Group, Modal, SegmentedControl, Stack, TextInput } from "@mantine/core";
import { isEmail, useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { useState } from "react";

import { inviteMember } from "./api";
import type { Invite } from "./types";

export function InviteMemberModal({ opened, onClose }: { opened: boolean; onClose: () => void }) {
  const [isSending, setIsSending] = useState(false);
  const form = useForm<Invite>({
    mode: "uncontrolled",
    initialValues: { email: "", role: "member" },
    validate: { email: isEmail("Enter a valid email address") },
  });

  const close = () => {
    form.reset();
    onClose();
  };

  const send = async (invite: Invite) => {
    setIsSending(true);
    try {
      await inviteMember(invite);
      notifications.show({ title: "Invite sent", message: `Invitation sent to ${invite.email}`, color: "green" });
      close();
    } catch {
      notifications.show({ title: "Invite failed", message: `Could not invite ${invite.email}`, color: "red" });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <Modal opened={opened} onClose={close} title="Invite teammate" centered>
      <form onSubmit={form.onSubmit(send)}>
        <Stack gap="md">
          <TextInput
            label="Email"
            placeholder="name@company.com"
            withAsterisk
            key={form.key("email")}
            {...form.getInputProps("email")}
          />
          <SegmentedControl
            data={[
              { label: "Member", value: "member" },
              { label: "Admin", value: "admin" },
            ]}
            key={form.key("role")}
            {...form.getInputProps("role")}
          />
          <Group justify="flex-end" gap="sm">
            <Button variant="default" onClick={close}>
              Cancel
            </Button>
            <Button type="submit" loading={isSending}>
              Send invite
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
TSX
cat > src/team/TeamPage.tsx <<'TSX'
import { Badge, Button, Table } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";

import { PageHeader } from "../layout/PageHeader";
import { InviteMemberModal } from "./InviteMemberModal";
import type { Member } from "./types";

export function TeamPage({ members }: { members: Member[] }) {
  const [inviteOpened, invite] = useDisclosure(false);

  return (
    <>
      <PageHeader
        title="Team"
        subtitle={`${members.length} members`}
        actions={<Button onClick={invite.open}>Invite teammate</Button>}
      />
      <InviteMemberModal opened={inviteOpened} onClose={invite.close} />
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
TSX
