#!/usr/bin/env bash
set -euo pipefail

INTERVAL_SECONDS="${BACKUP_INTERVAL_SECONDS:-86400}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-prodrive}"
POSTGRES_DB="${POSTGRES_DB:-prodrive}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
UPLOADS_PATH="${UPLOADS_PATH:-/uploads}"

mkdir -p "${BACKUP_DIR}"

while true; do
  TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
  DB_OUTPUT="${BACKUP_DIR}/prodrive_${TIMESTAMP}.sql.gz"
  UPLOADS_OUTPUT="${BACKUP_DIR}/uploads_${TIMESTAMP}.tar.gz"

  echo "[$(date -Iseconds)] Starting scheduled backup"
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${DB_OUTPUT}"
  tar -czf "${UPLOADS_OUTPUT}" -C "${UPLOADS_PATH}" . 2>/dev/null || echo "Uploads backup skipped"

  find "${BACKUP_DIR}" -name 'prodrive_*.sql.gz' -mtime +"${RETENTION_DAYS}" -delete
  find "${BACKUP_DIR}" -name 'uploads_*.tar.gz' -mtime +"${RETENTION_DAYS}" -delete
  echo "[$(date -Iseconds)] Backup complete"
  sleep "${INTERVAL_SECONDS}"
done
