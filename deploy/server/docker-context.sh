#!/usr/bin/env bash
# From the Mac: create a Docker context that drives SERVER's Docker Desktop over SSH (Tailscale).
# Usage: deploy/server/docker-context.sh <ssh-user> <server-tailscale-name-or-ip>
set -euo pipefail
USER_="$1"; HOST="$2"
docker context rm -f server >/dev/null 2>&1 || true
docker context create server --docker "host=ssh://${USER_}@${HOST}" --description "AGL PoC SERVER (Windows/WSL2)"
docker --context server info --format 'Server: {{.ServerVersion}} · OS: {{.OperatingSystem}} · CPUs: {{.NCPU}} · Mem: {{.MemTotal}}'
echo "use:  docker --context server ps     or    export DOCKER_CONTEXT=server"
