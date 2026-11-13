set -e
cd /app
git init -q
git add -A
git commit -q -m "Initial suppliers service"
git rev-parse HEAD > /etc/eval-base-sha
git checkout -q -b feature/supplier-contacts
cp -R /tmp/feature/. /app/
git add -A
git commit -q -m "Add supplier contacts and search"
git rev-parse HEAD > /etc/eval-feature-sha
chmod 444 /etc/eval-base-sha /etc/eval-feature-sha
