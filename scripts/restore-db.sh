#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <backup.sql.gz>"
  exit 1
fi

BACKUP_FILE="$1"
POSTGRES_USER="${POSTGRES_USER:-prodrive}"
POSTGRES_DB="${POSTGRES_DB:-prodrive}"
CONTAINER="${POSTGRES_CONTAINER:-prodrive-postgres}"

echo "Restoring ${BACKUP_FILE} into ${POSTGRES_DB}"
gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
echo "Restore complete"
