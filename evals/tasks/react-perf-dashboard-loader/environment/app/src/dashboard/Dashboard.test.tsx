import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { Dashboard } from "./Dashboard";
import { fakeApi } from "./fakeApi";
import { loadDashboard } from "./loadDashboard";

test("greets the user and lists the team's projects", async () => {
  render(<Dashboard api={fakeApi()} userId="u1" />);
  expect(await screen.findByText("Hello, Ada")).toBeTruthy();
  expect(screen.getByText("Delta")).toBeTruthy();
});

test("the embedded widget shows at most three projects", async () => {
  const data = await loadDashboard(fakeApi(), "u1", { embedded: true });
  expect(data.projects.map((project) => project.id)).toEqual(["p1", "p2", "p3"]);
});
