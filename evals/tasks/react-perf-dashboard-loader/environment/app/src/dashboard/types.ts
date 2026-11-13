export type User = { id: string; name: string; teamId: string };
export type Settings = { theme: "light" | "dark"; showAnnouncements: boolean };
export type Project = { id: string; name: string };
export type Announcement = { id: string; title: string };

export type DashboardData = {
  user: User;
  settings: Settings;
  projects: Project[];
};
