set -e
cd /app
git init -q
git add -A
git commit -q -m "Initial invoices service"
git rev-parse HEAD > /etc/eval-base-sha
git checkout -q -b feature/invoice-approval
cp -R /tmp/feature/. /app/
git add -A
git commit -q -m "Add invoice approval and overdue listing"
git rev-parse HEAD > /etc/eval-feature-sha
chmod 444 /etc/eval-base-sha /etc/eval-feature-sha
