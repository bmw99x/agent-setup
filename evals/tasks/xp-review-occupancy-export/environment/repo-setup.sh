set -e
cd /app
git init -q
git add -A
git commit -q -m "Meeting rooms: bookings and cancellation fees"
git rev-parse HEAD > /etc/eval-base-sha
git checkout -q -b feature/rooms-142-occupancy-csv
cp -R /tmp/feature/. /app/
git add -A
git commit -q -m "ROOMS-142: monthly occupancy report as CSV for finance"
git rev-parse HEAD > /etc/eval-feature-sha
chmod 444 /etc/eval-base-sha /etc/eval-feature-sha
