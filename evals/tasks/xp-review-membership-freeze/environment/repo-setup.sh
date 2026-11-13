set -e
cd /app
git init -q
git add -A
git commit -q -m "Memberships: plans, cancellation, plan changes"
git rev-parse HEAD > /etc/eval-base-sha
git checkout -q -b feature/membership-freeze
cp -R /tmp/feature/. /app/
git add -A
git commit -q -m "Let members freeze their membership"
git rev-parse HEAD > /etc/eval-feature-sha
chmod 444 /etc/eval-base-sha /etc/eval-feature-sha
