#!/bin/sh
# Builds the payouts history: main, !42 (feature/payout-scaffold) and !43 stacked on it
# (feature/payout-batching); publishes it to a local bare "origin" and clones it to /app on main.
set -e
work=/tmp/build
git init -q "$work"
cp -r /tmp/repo/main/. "$work"
cd "$work"
git add -A && git commit -qm "Payouts: routing, database and bank client; design doc"
git checkout -qb feature/payout-scaffold
cp -r /tmp/repo/scaffold/. . && git add -A && git commit -qm "feat(payouts): POST /payouts with ledger reservation and bank transfer"
git checkout -qb feature/payout-batching
cp -r /tmp/repo/batching/. . && git add -A && git commit -qm "feat(payouts): queue bank transfers for a batch worker"
git checkout -q main
mkdir -p /srv/git
git clone -q --bare "$work" /srv/git/payouts.git
git clone -q /srv/git/payouts.git /app
git -C /app rev-parse HEAD > /etc/eval-base-sha
git -C /app rev-parse origin/feature/payout-batching > /etc/eval-pinned-sha
git -C /app rev-parse origin/feature/payout-scaffold > /etc/eval-linked-sha
rm -rf "$work"
