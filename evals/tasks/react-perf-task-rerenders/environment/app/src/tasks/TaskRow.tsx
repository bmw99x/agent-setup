import { memo } from "react";

import type { Task } from "./types";

type Props = { task: Task };

/** One row of the task list. Memoized: lists run to several hundred rows. */
export const TaskRow = memo(function TaskRow({ task }: Props) {
  return (
    <li className={task.done ? "task task--done" : "task"}>
      <span className="task__title">{task.title}</span>
    </li>
  );
});
