import { useEffect, useState } from "react";

import type { DashboardApi } from "./api";
import { loadDashboard } from "./loadDashboard";
import type { DashboardData } from "./types";

type Props = { api: DashboardApi; userId: string; embedded?: boolean };

export function Dashboard({ api, userId, embedded = false }: Props) {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadDashboard(api, userId, { embedded }).then((loaded) => {
      if (!cancelled) setData(loaded);
    });
    return () => {
      cancelled = true;
    };
  }, [api, userId, embedded]);

  if (!data) return <p>Loading…</p>;

  return (
    <main className={data.settings.theme}>
      <h1>Hello, {data.user.name}</h1>
      <section aria-label="Projects">
        <h2>Projects</h2>
        <ul>
          {data.projects.map((project) => (
            <li key={project.id}>{project.name}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
