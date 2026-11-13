# Duplicate member registration

`POST /members` in the clubhouse API (`/app`) registers a member. Emails are stored lowercased, and the `members.email` column is unique.

Registering an email that is already taken (in any letter case) currently crashes with a 500. It should return **409** with the body `{"detail": "email already registered"}`. Every other registration should keep working as it does now.

Keep the existing tests in `/app/tests` passing and add a test for the duplicate case.
