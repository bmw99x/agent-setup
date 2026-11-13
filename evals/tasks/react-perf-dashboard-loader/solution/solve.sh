#!/bin/bash
set -euo pipefail
cd /app
cat > src/dashboard/types.ts <<'TS'
export type User = { id: string; name: string; teamId: string };
export type Settings = { theme: "light" | "dark"; showAnnouncements: boolean };
export type Project = { id: string; name: string };
export type Announcement = { id: string; title: string };

export type DashboardData = {
  user: User;
  settings: Settings;
  projects: Project[];
  announcements: Announcement[];
};
TS
cat > src/dashboard/loadDashboard.ts <<'TS'
import type { DashboardApi } from "./api";
import type { Announcement, DashboardData } from "./types";

export type LoadOptions = {
  /** The compact widget embedded in other apps: shows at most three projects. */
  embedded?: boolean;
};

const EMBEDDED_PROJECT_LIMIT = 3;
const ANNOUNCEMENTS_FLAG = "announcements";
const NO_ANNOUNCEMENTS: Announcement[] = [];

export async function loadDashboard(
  api: DashboardApi,
  userId: string,
  { embedded = false }: LoadOptions = {},
): Promise<DashboardData> {
  // Each request starts as soon as its inputs are known.
  const userPromise = api.getUser(userId);
  const settingsPromise = api.getSettings(userId);
  const projectsPromise = userPromise.then((user) => api.getProjects(user.teamId));
  const announcementsPromise = embedded
    ? Promise.resolve(NO_ANNOUNCEMENTS)
    : loadAnnouncements(api, userPromise, settingsPromise);

  const [user, settings, projects, announcements] = await Promise.all([
    userPromise,
    settingsPromise,
    projectsPromise,
    announcementsPromise,
  ]);

  return {
    user,
    settings,
    projects: embedded ? projects.slice(0, EMBEDDED_PROJECT_LIMIT) : projects,
    announcements,
  };
}

async function loadAnnouncements(
  api: DashboardApi,
  userPromise: ReturnType<DashboardApi["getUser"]>,
  settingsPromise: ReturnType<DashboardApi["getSettings"]>,
): Promise<Announcement[]> {
  const [enabled, user, settings] = await Promise.all([api.getFlag(ANNOUNCEMENTS_FLAG), userPromise, settingsPromise]);
  if (!enabled || !settings.showAnnouncements) return NO_ANNOUNCEMENTS;
  return api.getAnnouncements(user.teamId);
}
TS
python3 - <<'PY'
from pathlib import Path
path = Path("src/dashboard/Dashboard.tsx")
src = path.read_text()
src = src.replace("""      </section>
    </main>""", """      </section>
      {data.announcements.length > 0 && (
        <section aria-label="Announcements">
          <h2>Announcements</h2>
          <ul>
            {data.announcements.map((announcement) => (
              <li key={announcement.id}>{announcement.title}</li>
            ))}
          </ul>
        </section>
      )}
    </main>""")
path.write_text(src)
PY
