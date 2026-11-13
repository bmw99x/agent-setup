# Tick off and remove tasks

The task list (`/app/src/tasks/TaskList.tsx`, rows rendered by `TaskRow.tsx`) can only add tasks. Make it useful:

- Each row gets a checkbox to mark the task done or not done. The checkbox's accessible name is the task title.
- Each row gets a **Remove** button that deletes that task.
- Above the list, show how many tasks are left as `<p>N remaining</p>` (e.g. `3 remaining`), counting tasks that are not done. It updates as tasks are added, ticked or removed.

Teams keep several hundred tasks in one list. Keep `npm test` and `npm run typecheck` passing.
