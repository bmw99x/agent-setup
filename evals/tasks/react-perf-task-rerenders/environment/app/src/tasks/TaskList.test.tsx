import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { TaskList } from "./TaskList";

test("adds a task from the form", () => {
  render(<TaskList initialTasks={[{ id: "1", title: "Write docs", done: false }]} />);
  fireEvent.change(screen.getByLabelText("New task"), { target: { value: "Ship it" } });
  fireEvent.click(screen.getByRole("button", { name: "Add" }));
  expect(screen.getAllByRole("listitem")).toHaveLength(2);
  expect(screen.getByText("Ship it")).toBeTruthy();
});
