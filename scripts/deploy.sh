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

echo "[5/6] Restarting services..."
docker compose up -d

echo "[6/6] Health check..."
sleep 3
docker compose ps

echo "✓ Deploy complete."
