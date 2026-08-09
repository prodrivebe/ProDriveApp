#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

BACKUP_DIR="${BACKUP_DIR:-./backups}"
UPLOADS_PATH="${UPLOADS_PATH:-./uploads_data_mount}"

echo "=== ProDrive full backup ==="
./scripts/backup-db.sh

if docker volume inspect prodriveapp_uploads_data >/dev/null 2>&1; then
  VOLUME_PATH="$(docker volume inspect prodriveapp_uploads_data --format '{{ .Mountpoint }}')"
  UPLOADS_PATH="${VOLUME_PATH}" ./scripts/backup-uploads.sh
elif [ -d "${UPLOADS_PATH}" ]; then
  UPLOADS_PATH="${UPLOADS_PATH}" ./scripts/backup-uploads.sh
else
  echo "Skipping uploads backup: mount uploads volume or set UPLOADS_PATH"
fi

echo "=== Backup finished ==="
