#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
POSTGRES_USER="${POSTGRES_USER:-prodrive}"
POSTGRES_DB="${POSTGRES_DB:-prodrive}"
CONTAINER="${POSTGRES_CONTAINER:-prodrive-postgres}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

mkdir -p "${BACKUP_DIR}"
OUTPUT="${BACKUP_DIR}/prodrive_${TIMESTAMP}.sql.gz"

echo "Creating database backup ${OUTPUT}"
docker exec "${CONTAINER}" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${OUTPUT}"
echo "Database backup complete"

if [ -d "${BACKUP_DIR}" ] && [ "${RETENTION_DAYS}" -gt 0 ]; then
  find "${BACKUP_DIR}" -name 'prodrive_*.sql.gz' -mtime +"${RETENTION_DAYS}" -delete
  echo "Pruned database backups older than ${RETENTION_DAYS} days"
fi
