import { MantineProvider } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import { render as rtlRender, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { TeamPage } from "../team/TeamPage";

const render = (ui: JSX.Element) =>
  rtlRender(
    <MantineProvider env="test">
      <Notifications />
      {ui}
    </MantineProvider>,
  );

afterEach(() => vi.unstubAllGlobals());

const members = [{ id: "1", name: "Ada Lovelace", email: "ada@acme.test", role: "admin" as const }];

function stubFetch() {
  const fetchMock = vi.fn(async () => new Response(null, { status: 204 }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function openDialog() {
  render(<TeamPage members={members} />);
  fireEvent.click(screen.getByRole("button", { name: /invite teammate/i }));
  return screen.findByRole("dialog");
}

function emailInput(dialog: HTMLElement) {
  return within(dialog).getByRole("textbox", { name: /email/i }) as HTMLInputElement;
}

function sendButton(dialog: HTMLElement) {
  return within(dialog).getByRole("button", { name: /send/i });
}

test("invalid email is flagged on the field and nothing is sent", async () => {
  const fetchMock = stubFetch();
  const dialog = await openDialog();
  fireEvent.change(emailInput(dialog), { target: { value: "not-an-email" } });
  fireEvent.click(sendButton(dialog));
  await waitFor(() => expect(emailInput(dialog).getAttribute("aria-invalid")).toBe("true"));
  expect(fetchMock).not.toHaveBeenCalled();
});

test("valid invite is sent as a member, the dialog closes and the admin is told", async () => {
  const fetchMock = stubFetch();
  const dialog = await openDialog();
  fireEvent.change(emailInput(dialog), { target: { value: "sam@acme.test" } });
  fireEvent.click(sendButton(dialog));
  await waitFor(() => expect(fetchMock).toHaveBeenCalled());
  const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
  expect(url).toBe("/api/team/invites");
  expect(JSON.parse(String(init.body))).toEqual({ email: "sam@acme.test", role: "member" });
  await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  expect(await screen.findByText((content) => content.includes("sam@acme.test"))).toBeTruthy();
});
