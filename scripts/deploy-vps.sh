#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
test -f .env || { echo "Missing server-side .env" >&2; exit 1; }

docker compose -f compose.production.yaml config --quiet
docker compose -f compose.production.yaml build backend frontend
docker compose -f compose.production.yaml up -d --wait db redis mailpit
docker compose -f compose.production.yaml run --rm backend python manage.py migrate --noinput
docker compose -f compose.production.yaml run --rm backend python manage.py collectstatic --noinput
docker compose -f compose.production.yaml up -d --wait --no-build backend frontend caddy
docker compose -f compose.production.yaml ps
