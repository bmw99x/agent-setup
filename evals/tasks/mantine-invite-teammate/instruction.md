# Invite a teammate

The **Invite teammate** button on the team page (`src/team/TeamPage.tsx`) does nothing yet. Make it open a dialog where an admin can invite someone.

- Fields: **Email** (required, must be a valid address) and **Role**, either Member or Admin, defaulting to Member.
- **Cancel** and **Send invite** buttons sit together at the bottom right of the dialog.
- If the email is missing or invalid, show the error under the field and send nothing.
- Send the invite with `inviteMember` from `src/team/api.ts`. While it's sending, the Send button shows it's busy. When it succeeds, close the dialog, clear the form and let the admin know the invite went out, naming the email address. The app shell already mounts Mantine's `<Notifications />` (see `src/main.tsx`).

Keep `npm test` and `npm run typecheck` passing.
