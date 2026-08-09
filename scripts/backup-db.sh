#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
POSTGRES_USER="${POSTGRES_USER:-prodrive}"
POSTGRES_DB="${POSTGRES_DB:-prodrive}"
CONTAINER="${POSTGRES_CONTAINER:-prodrive-postgres}"

mkdir -p "${BACKUP_DIR}"
OUTPUT="${BACKUP_DIR}/prodrive_${TIMESTAMP}.sql.gz"

echo "Creating backup ${OUTPUT}"
docker exec "${CONTAINER}" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${OUTPUT}"
echo "Backup complete"
