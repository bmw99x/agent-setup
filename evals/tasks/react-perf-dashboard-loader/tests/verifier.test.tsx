import { render, screen, within } from "@testing-library/react";
import { expect, test } from "vitest";

import type { DashboardApi } from "../dashboard/api";
import { Dashboard } from "../dashboard/Dashboard";
import { loadDashboard } from "../dashboard/loadDashboard";

type Method = keyof DashboardApi;
const USER = { id: "u1", name: "Ada", teamId: "t1" };
const PROJECTS = [1, 2, 3, 4, 5].map((n) => ({ id: `p${n}`, name: `Project ${n}` }));
const ANNOUNCEMENTS = [{ id: "a1", title: "Offsite next Friday" }];

/** Every request stays in flight until the test answers it, so call order exposes waterfalls. */
function controlledApi() {
  const calls: { method: Method; args: unknown[] }[] = [];
  const waiting: { method: Method; resolve: (value: unknown) => void }[] = [];
  const method = (name: Method) => (...args: unknown[]) => {
    calls.push({ method: name, args });
    return new Promise((resolve) => waiting.push({ method: name, resolve }));
  };
  const api = {
    getUser: method("getUser"),
    getSettings: method("getSettings"),
    getProjects: method("getProjects"),
    getFlag: method("getFlag"),
    getAnnouncements: method("getAnnouncements"),
  } as unknown as DashboardApi;
  const answer = (name: Method, value: unknown) => {
    for (const entry of waiting.filter((w) => w.method === name)) entry.resolve(value);
  };
  const started = () => calls.map((call) => call.method);
  return { api, calls, answer, started };
}

function instantApi({ flag = true, showAnnouncements = true } = {}) {
  const calls: Method[] = [];
  const api: DashboardApi = {
    getUser: async () => (calls.push("getUser"), USER),
    getSettings: async () => (calls.push("getSettings"), { theme: "light", showAnnouncements }),
    getProjects: async () => (calls.push("getProjects"), PROJECTS),
    getFlag: async () => (calls.push("getFlag"), flag),
    getAnnouncements: async () => (calls.push("getAnnouncements"), ANNOUNCEMENTS),
  };
  return { api, calls };
}

async function settle() {
  for (let i = 0; i < 20; i++) await new Promise((resolve) => setTimeout(resolve, 0));
}

test("independent requests start before any response arrives", async () => {
  const { api, started } = controlledApi();
  void loadDashboard(api, "u1");
  await settle();
  expect(started()).toContain("getUser");
  expect(started()).toContain("getSettings");
});

test("team requests start as soon as the user arrives, not after unrelated requests", async () => {
  const { api, calls, answer } = controlledApi();
  void loadDashboard(api, "u1");
  await settle();
  answer("getUser", USER);
  await settle();
  const projectCall = calls.find((call) => call.method === "getProjects");
  expect(projectCall, "getProjects should not wait for getSettings/getFlag").toBeDefined();
  expect(projectCall?.args[0]).toBe("t1");
});

test("embedded widget never requests the flag or announcements", async () => {
  const { api, calls } = instantApi();
  await loadDashboard(api, "u1", { embedded: true });
  expect(calls).not.toContain("getFlag");
  expect(calls).not.toContain("getAnnouncements");
});

test("announcements are returned when the flag and the setting are on", async () => {
  const { api } = instantApi();
  const data = (await loadDashboard(api, "u1")) as Record<string, unknown>;
  expect(data.announcements).toEqual(ANNOUNCEMENTS);
  expect(data.projects).toEqual(PROJECTS);
});

test("announcements are empty when the flag is off", async () => {
  const { api } = instantApi({ flag: false });
  const data = (await loadDashboard(api, "u1")) as Record<string, unknown>;
  expect(data.announcements).toEqual([]);
});

test("announcements are empty when the user switched them off", async () => {
  const { api } = instantApi({ showAnnouncements: false });
  const data = (await loadDashboard(api, "u1")) as Record<string, unknown>;
  expect(data.announcements).toEqual([]);
});

test("embedded widget gets no announcements and at most three projects", async () => {
  const { api } = instantApi();
  const data = (await loadDashboard(api, "u1", { embedded: true })) as Record<string, unknown>;
  expect(data.announcements).toEqual([]);
  expect((data.projects as unknown[]).length).toBe(3);
});

test("dashboard lists announcement titles", async () => {
  const { api } = instantApi();
  render(<Dashboard api={api} userId="u1" />);
  const section = await screen.findByRole("region", { name: "Announcements" });
  expect(within(section).getByText("Offsite next Friday")).toBeTruthy();
});
