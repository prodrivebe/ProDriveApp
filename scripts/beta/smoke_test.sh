#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000/api/v1}"

echo "ProDrive beta smoke test against ${API_BASE}"

curl -fsS "${API_BASE}/health" | tee /tmp/prodrive-health.json
echo

curl -fsS "${API_BASE}/health/ready" | tee /tmp/prodrive-ready.json
echo

TOKEN="$(
  curl -fsS -X POST "${API_BASE}/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@example.com","password":"Admin123!"}' \
    | python -c "import sys, json; print(json.load(sys.stdin)['data']['access_token'])"
)"

curl -fsS -H "Authorization: Bearer ${TOKEN}" "${API_BASE}/planning/board" | tee /tmp/prodrive-board.json
echo

curl -fsS -H "Authorization: Bearer ${TOKEN}" "${API_BASE}/orders?page=1&page_size=5" | tee /tmp/prodrive-orders.json
echo

echo "Smoke test completed successfully"
