import type { DashboardApi } from "./api";

export function fakeApi(overrides: Partial<DashboardApi> = {}): DashboardApi {
  return {
    getUser: async (userId) => ({ id: userId, name: "Ada", teamId: "t1" }),
    getSettings: async () => ({ theme: "light", showAnnouncements: true }),
    getProjects: async () => [
      { id: "p1", name: "Apollo" },
      { id: "p2", name: "Borealis" },
      { id: "p3", name: "Cobalt" },
      { id: "p4", name: "Delta" },
    ],
    getFlag: async () => false,
    getAnnouncements: async () => [],
    ...overrides,
  };
}
