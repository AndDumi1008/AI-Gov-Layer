#!/bin/bash
# Runs once at database initialisation (postgres image entrypoint). Sets the gateway role password from the
# environment so no credential lives in the repository (PD-30).
set -euo pipefail
: "${AGL_GATEWAY_DB_PASSWORD:?AGL_GATEWAY_DB_PASSWORD must be set in stack/.env}"
case "$AGL_GATEWAY_DB_PASSWORD" in *changeme*|*placeholder*) echo "refusing placeholder gateway password; edit stack/.env" >&2; exit 1;; esac
psql -v ON_ERROR_STOP=1 -U postgres -d postgres -c "alter role agl_gateway password '$(printf %s "$AGL_GATEWAY_DB_PASSWORD" | sed "s/'/''/g")';"
echo "gateway role password set from environment"
