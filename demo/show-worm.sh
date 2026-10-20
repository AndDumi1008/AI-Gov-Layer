#!/usr/bin/env bash
# Act 6 helper: show the WORM audit store live (segments, retention, versions) and attempt a delete.
# Runs mc on the engine selected by DOCKER_CONTEXT (server for the demo). Credentials from AGL_ENV_FILE or stack/.env.
set -euo pipefail
cd "$(dirname "$0")/.."
ENV_FILE="${AGL_ENV_FILE:-stack/.env}"
if [ "${DOCKER_CONTEXT:-}" = "server" ] && [ ! -f "${AGL_ENV_FILE:-}" ]; then ENV_FILE=$(mktemp); scp -q server:D:/Projects/AI-Gov-Layer/stack/.env "$ENV_FILE"; trap 'rm -f "$ENV_FILE"' EXIT; fi
U=$(grep -E '^MINIO_ROOT_USER=' "$ENV_FILE" | cut -d= -f2); P=$(grep -E '^MINIO_ROOT_PASSWORD=' "$ENV_FILE" | cut -d= -f2)
MC=$(grep -oE 'bitnamilegacy/minio-client@sha256:[0-9a-f]+' stack/docker-compose.yml | head -1)
docker run --rm --network agl_agl-net --entrypoint sh "$MC" -c "
mc alias set a http://minio:9000 '$U' '$P' >/dev/null
echo '== bucket agl-audit: lock configuration'; mc retention info a/agl-audit 2>&1 | sed 's/^/   /'
echo; echo '== newest segments'; mc ls --recursive a/agl-audit/segments | tail -5 | sed 's/^/   /'
OBJ=\$(mc ls --recursive a/agl-audit/segments | tail -1 | awk '{print \$NF}')
echo; echo \"== retention on the newest segment (\$OBJ)\"; mc retention info a/agl-audit/segments/\$OBJ 2>&1 | grep -E 'Mode|expir' | sed 's/^/   /'
echo; echo '== versions'; mc ls --versions a/agl-audit/segments/\$OBJ | sed 's/^/   /'
echo; echo '== attempt: delete all versions as the storage administrator'; mc rm --versions --force a/agl-audit/segments/\$OBJ 2>&1 | sed 's/^/   /' || true
echo; echo '== still there'; mc ls --versions a/agl-audit/segments/\$OBJ | grep -vc DEL | sed 's/^/   real versions: /'
echo; echo '== anchors (second store, separate credentials)'; mc alias set b http://minio-anchor:9000 '$(grep -E '^ANCHOR_ROOT_USER=' "$ENV_FILE"|cut -d= -f2)' '$(grep -E '^ANCHOR_ROOT_PASSWORD=' "$ENV_FILE"|cut -d= -f2)' >/dev/null; mc ls --recursive b/agl-anchor | tail -3 | sed 's/^/   /'
"
