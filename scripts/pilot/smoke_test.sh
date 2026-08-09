#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost/api/v1}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin123!}"

echo "ProDrive pilot smoke test against ${API_BASE}"

curl -fsS "${API_BASE}/health" | tee /tmp/prodrive-health.json
echo

curl -fsS "${API_BASE}/health/ready" | tee /tmp/prodrive-ready.json
echo

curl -fsS "${API_BASE}/health/ops" | tee /tmp/prodrive-ops.json
echo

TOKEN="$(
  curl -fsS -X POST "${API_BASE}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" \
    | python -c "import sys, json; print(json.load(sys.stdin)['data']['access_token'])"
)"

curl -fsS -H "Authorization: Bearer ${TOKEN}" "${API_BASE}/planning/board" | tee /tmp/prodrive-board.json
echo

curl -fsS -H "Authorization: Bearer ${TOKEN}" "${API_BASE}/orders?page=1&page_size=5" | tee /tmp/prodrive-orders.json
echo

curl -fsS -H "Authorization: Bearer ${TOKEN}" "${API_BASE}/reports/kpi" | tee /tmp/prodrive-kpi.json
echo

echo "Pilot smoke test completed successfully"
