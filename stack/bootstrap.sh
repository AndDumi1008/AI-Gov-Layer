#!/usr/bin/env bash
# First-time setup: .env, DNS zone, then bring the stack up with the chosen profiles.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example — edit passwords (and ANTHROPIC_API_KEY) before using on SERVER"; }
set -a; . ./.env; set +a
sed "s/__SERVER_TS_IP__/${SERVER_TS_IP}/g" dns/zones/db.shortandsweet.home.ro.template > dns/zones/db.shortandsweet.home.ro
mkdir -p ../evidence
PROFILES="${*:---profile mock}"
echo "docker compose $PROFILES up -d --build"
# shellcheck disable=SC2086
docker compose $PROFILES up -d --build
echo "waiting for gateway..."
for i in $(seq 1 60); do curl -fsS "http://${BIND_IP}:4000/healthz" >/dev/null 2>&1 && { echo "gateway up at http://${BIND_IP}:4000"; exit 0; }; sleep 2; done
echo "gateway did not come up; docker compose logs gateway"; exit 1
