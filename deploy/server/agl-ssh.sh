#!/usr/bin/env bash
# Run a command on SERVER inside Git Bash with an environment where the Docker CLI works from SSH:
#  - PATH without Docker Desktop's credential helper (otherwise the CLI calls it and it fails outside the
#    interactive logon session: "A specified logon session does not exist")
#  - DOCKER_CONFIG pointing to a plain config ({}), so no credential store is used (public images only)
#  - cwd = the repository checkout on D:
# Usage: deploy/server/agl-ssh.sh 'docker compose -f stack/docker-compose.yml ps'
set -euo pipefail
CMD="$*"
ssh -o BatchMode=yes -o ConnectTimeout=15 server "\"C:\\Program Files\\Git\\bin\\bash.exe\" -lc 'export PATH=/c/Program\\ Files/Docker/Docker/resources/bin:/c/Windows/System32:/c/Windows:/c/Program\\ Files/Git/bin:/c/Program\\ Files/Git/usr/bin; export DOCKER_CONFIG=/d/agl-docker-config; export MSYS_NO_PATHCONV=1; cd /d/Projects/AI-Gov-Layer && $CMD'" 2>&1 | tr -d '\r'
