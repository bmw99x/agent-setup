import type { Announcement, Project, Settings, User } from "./types";

/** Backend client for the dashboard. Every call is one HTTP round trip. */
export interface DashboardApi {
  getUser(userId: string): Promise<User>;
  getSettings(userId: string): Promise<Settings>;
  getProjects(teamId: string): Promise<Project[]>;
  getFlag(name: string): Promise<boolean>;
  getAnnouncements(teamId: string): Promise<Announcement[]>;
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} failed with ${response.status}`);
  return (await response.json()) as T;
}

export const httpDashboardApi: DashboardApi = {
  getUser: (userId) => getJson(`/api/users/${userId}`),
  getSettings: (userId) => getJson(`/api/users/${userId}/settings`),
  getProjects: (teamId) => getJson(`/api/teams/${teamId}/projects`),
  getFlag: (name) => getJson(`/api/flags/${name}`),
  getAnnouncements: (teamId) => getJson(`/api/teams/${teamId}/announcements`),
};
