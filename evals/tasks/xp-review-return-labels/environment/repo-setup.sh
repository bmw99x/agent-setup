set -e
cd /app
git init -q
git add -A
git commit -q -m "Parcel dispatch: labels, manifest, notifications"
git rev-parse HEAD > /etc/eval-base-sha
git checkout -q -b feature/customer-returns
cp -R /tmp/feature/. /app/
git add -A
git commit -q -m "Add customer returns with prepaid return labels"
git rev-parse HEAD > /etc/eval-feature-sha
chmod 444 /etc/eval-base-sha /etc/eval-feature-sha
