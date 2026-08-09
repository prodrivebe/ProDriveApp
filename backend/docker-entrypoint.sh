#!/bin/sh
set -e

alembic upgrade head

if [ "${APP_ENV:-development}" = "development" ]; then
  python -m app.scripts.seed_dev
fi

if [ "${SEED_BETA:-false}" = "true" ]; then
  python -m app.scripts.seed_beta
fi

exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
