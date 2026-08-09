#!/usr/bin/env bash
set -euo pipefail

if [ -z "${PUBLIC_DOMAIN:-}" ]; then
  echo "Set PUBLIC_DOMAIN before running setup-ssl.sh" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

mkdir -p deployment/nginx/ssl deployment/certbot/www

echo "1. Start stack on HTTP only and obtain certificates with certbot."
echo "2. Copy fullchain.pem and privkey.pem into deployment/nginx/ssl/."
echo "3. Render SSL nginx config:"
echo "   envsubst '\$PUBLIC_DOMAIN' < deployment/nginx/conf.d/prodrive-ssl.conf.template > deployment/nginx/conf.d/prodrive-ssl.conf"
echo "4. Rebuild web image with SSL config mounted or replace prodrive.conf."
echo
echo "Example certbot command (host-installed certbot):"
echo "  certbot certonly --webroot -w ${ROOT_DIR}/deployment/certbot/www -d ${PUBLIC_DOMAIN}"
