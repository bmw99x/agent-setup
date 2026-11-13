import type { DashboardApi } from "./api";
import type { DashboardData } from "./types";

export type LoadOptions = {
  /** The compact widget embedded in other apps: shows at most three projects. */
  embedded?: boolean;
};

const EMBEDDED_PROJECT_LIMIT = 3;

export async function loadDashboard(
  api: DashboardApi,
  userId: string,
  { embedded = false }: LoadOptions = {},
): Promise<DashboardData> {
  const user = await api.getUser(userId);
  const settings = await api.getSettings(userId);
  const projects = await api.getProjects(user.teamId);

  return {
    user,
    settings,
    projects: embedded ? projects.slice(0, EMBEDDED_PROJECT_LIMIT) : projects,
  };
}
