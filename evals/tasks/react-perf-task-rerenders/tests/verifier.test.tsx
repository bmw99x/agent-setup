import { fireEvent, render, screen, within } from "@testing-library/react";
import { Profiler } from "react";
import { beforeEach, expect, test, vi } from "vitest";

import { TaskList } from "../tasks/TaskList";
import type { Task } from "../tasks/types";

const renders = vi.hoisted(() => ({ rows: 0 }));

// Count every render of TaskRow, keeping whatever memoization the project gave it.
vi.mock("../tasks/TaskRow", async (importOriginal) => {
  const mod = await importOriginal<Record<string, any>>();
  const React = await import("react");
  const original = mod.TaskRow;
  if (!original) return mod;
  const isMemo = original.$$typeof === Symbol.for("react.memo");
  const inner = isMemo ? original.type : original;
  function CountedTaskRow(props: Record<string, unknown>) {
    renders.rows += 1;
    return React.createElement(inner, props);
  }
  return { ...mod, TaskRow: isMemo ? React.memo(CountedTaskRow, original.compare ?? undefined) : CountedTaskRow };
});

const TASKS: Task[] = Array.from({ length: 200 }, (_, i) => ({ id: `t${i + 1}`, title: `Task ${i + 1}`, done: false }));

beforeEach(() => {
  renders.rows = 0;
});

function rowOf(title: string) {
  const row = screen.getByRole("checkbox", { name: title }).closest("li");
  if (!row) throw new Error(`no <li> around the checkbox for ${title}`);
  return row as HTMLElement;
}

test("ticking one task re-renders only that row", () => {
  render(<TaskList initialTasks={TASKS} />);
  renders.rows = 0;
  fireEvent.click(screen.getByRole("checkbox", { name: "Task 5" }));
  expect(renders.rows, "TaskRow renders after ticking one of 200 tasks").toBeLessThanOrEqual(2);
});

test("removing one task re-renders no other row", () => {
  render(<TaskList initialTasks={TASKS} />);
  renders.rows = 0;
  fireEvent.click(within(rowOf("Task 5")).getByRole("button", { name: /remove/i }));
  expect(renders.rows, "TaskRow renders after removing one of 200 tasks").toBeLessThanOrEqual(1);
});

test("typing a new task title re-renders no row", () => {
  render(<TaskList initialTasks={TASKS} />);
  renders.rows = 0;
  fireEvent.change(screen.getByLabelText("New task"), { target: { value: "B" } });
  expect(renders.rows, "TaskRow renders while typing in the new-task field").toBe(0);
});

test("ticking a task commits once (remaining count derived during render)", () => {
  const commits: string[] = [];
  render(
    <Profiler id="tasks" onRender={(_id, phase) => commits.push(phase)}>
      <TaskList initialTasks={TASKS.slice(0, 5)} />
    </Profiler>,
  );
  commits.length = 0;
  fireEvent.click(screen.getByRole("checkbox", { name: "Task 2" }));
  expect(screen.getByText("4 remaining")).toBeTruthy();
  expect(commits, "commits after one tick").toHaveLength(1);
});

test("ticking marks the task done and updates the count", () => {
  render(<TaskList initialTasks={TASKS.slice(0, 3)} />);
  expect(screen.getByText("3 remaining")).toBeTruthy();
  const box = screen.getByRole("checkbox", { name: "Task 2" }) as HTMLInputElement;
  fireEvent.click(box);
  expect(box.checked).toBe(true);
  expect(screen.getByText("2 remaining")).toBeTruthy();
  fireEvent.click(box);
  expect(box.checked).toBe(false);
  expect(screen.getByText("3 remaining")).toBeTruthy();
});

test("remove deletes the task and updates the count", () => {
  render(<TaskList initialTasks={TASKS.slice(0, 3)} />);
  fireEvent.click(within(rowOf("Task 2")).getByRole("button", { name: /remove/i }));
  expect(screen.queryByRole("checkbox", { name: "Task 2" })).toBeNull();
  expect(screen.getAllByRole("listitem")).toHaveLength(2);
  expect(screen.getByText("2 remaining")).toBeTruthy();
});

test("adding a task updates the count", () => {
  render(<TaskList initialTasks={TASKS.slice(0, 3)} />);
  fireEvent.change(screen.getByLabelText("New task"), { target: { value: "Ship it" } });
  fireEvent.click(screen.getByRole("button", { name: "Add" }));
  expect(screen.getByRole("checkbox", { name: "Ship it" })).toBeTruthy();
  expect(screen.getByText("4 remaining")).toBeTruthy();
});
