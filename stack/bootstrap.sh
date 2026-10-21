#!/usr/bin/env bash
# First-time setup: .env, DNS zone, then bring the stack up with the chosen profiles.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example — edit passwords before using on SERVER"; }
# content store key (PD-50): generated once, never committed; a missing key stops every model request (fail closed)
if ! grep -qE '^AGL_CONTENT_KEY=.+' .env; then
  key=$(openssl rand -base64 32)
  if grep -qE '^AGL_CONTENT_KEY=' .env; then sed -i.bak "s|^AGL_CONTENT_KEY=.*|AGL_CONTENT_KEY=${key}|" .env && rm -f .env.bak; else echo "AGL_CONTENT_KEY=${key}" >> .env; fi
  echo "generated AGL_CONTENT_KEY in .env (back it up: without it stored prompts cannot be read)"
fi
set -a; . ./.env; set +a
case "${POSTGRES_PASSWORD}${AGL_GATEWAY_DB_PASSWORD}${MINIO_ROOT_PASSWORD}${ANCHOR_ROOT_PASSWORD}" in *changeme*)
  if [ "${AGL_ALLOW_PLACEHOLDERS:-}" != "1" ]; then echo "stack/.env still has placeholder passwords. Edit it, or for a throw-away laptop run: AGL_ALLOW_PLACEHOLDERS=1 ./bootstrap.sh"; exit 1; fi;;
esac
sed "s/__SERVER_TS_IP__/${SERVER_TS_IP}/g" dns/zones/db.shortandsweet.home.ro.template > dns/zones/db.shortandsweet.home.ro
mkdir -p ../evidence
PROFILES="${*:---profile mock}"
# AGL_COMPOSE_EXTRA="-f docker-compose.gpu.yml" on SERVER (NVIDIA overlay)
EXTRA="${AGL_COMPOSE_EXTRA:-}"
echo "docker compose -f docker-compose.yml $EXTRA $PROFILES up -d --build"
# shellcheck disable=SC2086
docker compose -f docker-compose.yml $EXTRA $PROFILES up -d --build
echo "waiting for gateway..."
for i in $(seq 1 60); do curl -fsS "http://${BIND_IP}:4000/healthz" >/dev/null 2>&1 && { echo "gateway up at http://${BIND_IP}:4000"; exit 0; }; sleep 2; done
echo "gateway did not come up; docker compose logs gateway"; exit 1
