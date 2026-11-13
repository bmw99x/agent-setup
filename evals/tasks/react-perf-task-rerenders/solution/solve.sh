#!/bin/bash
set -euo pipefail
cd /app
cat > src/tasks/TaskRow.tsx <<'TS'
import { memo } from "react";

import type { Task } from "./types";

type Props = {
  task: Task;
  onToggle: (id: string) => void;
  onRemove: (id: string) => void;
};

/** One row of the task list. Memoized: lists run to several hundred rows. */
export const TaskRow = memo(function TaskRow({ task, onToggle, onRemove }: Props) {
  return (
    <li className={task.done ? "task task--done" : "task"}>
      <label>
        <input type="checkbox" checked={task.done} onChange={() => onToggle(task.id)} />
        <span className="task__title">{task.title}</span>
      </label>
      <button type="button" onClick={() => onRemove(task.id)}>
        Remove
      </button>
    </li>
  );
});
TS
cat > src/tasks/TaskList.tsx <<'TS'
import { useCallback, useState } from "react";

import { TaskRow } from "./TaskRow";
import type { Task } from "./types";

let nextId = 1;
const newTaskId = () => `new-${nextId++}`;

export function TaskList({ initialTasks }: { initialTasks: Task[] }) {
  const [tasks, setTasks] = useState(initialTasks);
  const [draft, setDraft] = useState("");
  const remaining = tasks.filter((task) => !task.done).length;

  const addTask = (event: React.FormEvent) => {
    event.preventDefault();
    const title = draft.trim();
    if (!title) return;
    setTasks((current) => [...current, { id: newTaskId(), title, done: false }]);
    setDraft("");
  };

  const toggleTask = useCallback((id: string) => {
    setTasks((current) => current.map((task) => (task.id === id ? { ...task, done: !task.done } : task)));
  }, []);

  const removeTask = useCallback((id: string) => {
    setTasks((current) => current.filter((task) => task.id !== id));
  }, []);

  return (
    <section>
      <form onSubmit={addTask}>
        <label>
          New task
          <input value={draft} onChange={(event) => setDraft(event.target.value)} />
        </label>
        <button type="submit">Add</button>
      </form>
      <p>{remaining} remaining</p>
      <ul>
        {tasks.map((task) => (
          <TaskRow key={task.id} task={task} onToggle={toggleTask} onRemove={removeTask} />
        ))}
      </ul>
    </section>
  );
}
TS
