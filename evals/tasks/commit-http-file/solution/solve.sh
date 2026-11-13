#!/bin/bash
set -e; cd /app
sed -i -e 's|^@baseUrl = .*|@baseUrl = {{BASE_URL}}|' -e 's|^@token = .*|@token = {{API_KEY}}|' requests/orders.http
git add requests/orders.http
git commit -q -m "chore(requests): add orders API http file"
