#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost/api/v1}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"

echo "ProDrive readiness check against ${API_BASE}"

READY_JSON="$(curl -fsS "${API_BASE}/health/ready" || true)"
if [ -z "${READY_JSON}" ]; then
  echo "Readiness probe failed"
  if [ -n "${ALERT_WEBHOOK_URL}" ]; then
    curl -fsS -X POST "${ALERT_WEBHOOK_URL}" \
      -H "Content-Type: application/json" \
      -d '{"text":"ProDrive readiness probe failed"}' || true
  fi
  exit 1
fi

echo "${READY_JSON}"
OPS_JSON="$(curl -fsS "${API_BASE}/health/ops")"
echo "${OPS_JSON}"

if echo "${OPS_JSON}" | grep -q '"maintenance_mode": true'; then
  echo "Maintenance mode is enabled"
  exit 2
fi

echo "Readiness check passed"
