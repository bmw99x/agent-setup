import { useState } from "react";

import { TaskRow } from "./TaskRow";
import type { Task } from "./types";

let nextId = 1;
const newTaskId = () => `new-${nextId++}`;

export function TaskList({ initialTasks }: { initialTasks: Task[] }) {
  const [tasks, setTasks] = useState(initialTasks);
  const [draft, setDraft] = useState("");

  const addTask = (event: React.FormEvent) => {
    event.preventDefault();
    const title = draft.trim();
    if (!title) return;
    setTasks((current) => [...current, { id: newTaskId(), title, done: false }]);
    setDraft("");
  };

  return (
    <section>
      <form onSubmit={addTask}>
        <label>
          New task
          <input value={draft} onChange={(event) => setDraft(event.target.value)} />
        </label>
        <button type="submit">Add</button>
      </form>
      <ul>
        {tasks.map((task) => (
          <TaskRow key={task.id} task={task} />
        ))}
      </ul>
    </section>
  );
}
