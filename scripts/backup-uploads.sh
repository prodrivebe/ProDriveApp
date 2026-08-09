#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
UPLOADS_PATH="${UPLOADS_PATH:-./uploads}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

mkdir -p "${BACKUP_DIR}"
OUTPUT="${BACKUP_DIR}/uploads_${TIMESTAMP}.tar.gz"

if [ ! -d "${UPLOADS_PATH}" ]; then
  echo "Uploads path not found: ${UPLOADS_PATH}" >&2
  exit 1
fi

echo "Creating uploads backup ${OUTPUT}"
tar -czf "${OUTPUT}" -C "${UPLOADS_PATH}" .
echo "Uploads backup complete"

if [ -d "${BACKUP_DIR}" ] && [ "${RETENTION_DAYS}" -gt 0 ]; then
  find "${BACKUP_DIR}" -name 'uploads_*.tar.gz' -mtime +"${RETENTION_DAYS}" -delete
  echo "Pruned uploads backups older than ${RETENTION_DAYS} days"
fi
