#!/usr/bin/env bash
# TCC Hub — production deploy script (Ubuntu)
# Usage on server (first time):
#   git clone https://github.com/azamatkajyrov26-lab/tcchub.git /opt/tcchub
#   cd /opt/tcchub && cp .env.example .env && nano .env   # fill secrets
#   bash scripts/deploy.sh
# Subsequent updates:  bash scripts/deploy.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/6] Pulling latest code..."
git pull --ff-only origin main

echo "[2/6] Verifying .env exists..."
[ -f .env ] || { echo "ERROR: .env missing. Copy from .env.example"; exit 1; }

echo "[3/6] Building containers..."
docker compose build

echo "[4/6] Running migrations + collectstatic..."
docker compose run --rm backend python manage.py migrate --noinput
docker compose run --rm backend python manage.py collectstatic --noinput

echo "[5/7] Restarting services..."
docker compose up -d

echo "[6/7] Reloading nginx (refresh upstream DNS for new backend IP)..."
# When backend container is recreated, nginx caches the old IP and returns 502.
# A reload re-resolves the 'backend' upstream via Docker DNS.
sleep 2
docker compose exec -T nginx nginx -s reload || docker compose restart nginx

echo "[7/7] Health check..."
sleep 3
docker compose ps
echo "  ↳ HTTP probe:"
for url in https://tc-cargo.kz/ https://tcchub.kz/; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$url" || echo "ERR")
  echo "    $url → $code"
done

echo "✓ Deploy complete."
