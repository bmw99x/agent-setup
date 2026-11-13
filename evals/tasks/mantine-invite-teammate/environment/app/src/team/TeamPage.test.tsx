import { screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { render } from "../test-utils";
import { TeamPage } from "./TeamPage";

test("lists team members", () => {
  render(<TeamPage members={[{ id: "1", name: "Ada Lovelace", email: "ada@acme.test", role: "admin" }]} />);
  expect(screen.getByText("ada@acme.test")).toBeTruthy();
});
