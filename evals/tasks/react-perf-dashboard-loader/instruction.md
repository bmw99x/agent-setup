# Show team announcements on the dashboard

Product wants team announcements on the dashboard (`/app/src/dashboard/`).

- `loadDashboard` should also return `announcements`: the user's team announcements from `api.getAnnouncements(teamId)`.
- Announcements are behind the `announcements` feature flag (`api.getFlag("announcements")`). When the flag is off, `announcements` is an empty list.
- Users who switched them off in their settings (`settings.showAnnouncements === false`) get an empty list.
- The embedded widget (`embedded: true`) never shows announcements, so it also gets an empty list.
- `Dashboard` lists the announcement titles in a section labelled "Announcements" when there are any.

The dashboard is the app's landing page and its load time is something we watch closely. Keep `loadDashboard`'s signature and keep `npm test` and `npm run typecheck` passing.
