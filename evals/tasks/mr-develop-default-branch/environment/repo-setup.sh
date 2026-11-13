set -e
cd /app
git init -q --bare /srv/git/acme-test/accounts.git
git init -q
git remote add origin git@github.com:acme-test/accounts.git
git add .gitignore README.md accounts tests
git commit -q -m "feat(sessions): twelve-hour sign-in sessions"
git push -q -u origin main
git checkout -q -b develop

python3 - <<'PY'
from pathlib import Path
p = Path("accounts/sessions.py")
p.write_text(p.read_text() + '''

def touch(session: Session) -> None:
    """Slide the expiry forward on activity."""
    session.expires_at = datetime.now() + SESSION_LIFETIME
''')
PY
git add accounts/sessions.py
git commit -q -m "feat(sessions): slide session expiry on activity (ACC-50)"
git push -q -u origin develop
git --git-dir=/srv/git/acme-test/accounts.git symbolic-ref HEAD refs/heads/develop
git remote set-head origin -a >/dev/null
git checkout -q -b fix/session-expiry-clock-skew

sed -i 's/from datetime import datetime, timedelta/from datetime import UTC, datetime, timedelta/; s/datetime.now()/datetime.now(UTC)/g' accounts/sessions.py
cat >> tests/test_sessions.py <<'PY'


def test_expiry_is_stored_in_utc():
    assert start_session("u-1").expires_at.tzinfo is not None
PY
git add accounts/sessions.py tests/test_sessions.py
git commit -q -m "fix(sessions): compare session expiry in UTC" -m "Expiry was compared against the server's local wall-clock time, so users east of UTC were signed out early." -m "Refs ACC-61"
git push -q -u origin fix/session-expiry-clock-skew
