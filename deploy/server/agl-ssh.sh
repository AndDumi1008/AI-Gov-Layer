#!/usr/bin/env bash
# Run a command on SERVER inside Git Bash, in an environment where the Docker CLI works from SSH.
#  - SSH's remote shell on Windows is cmd.exe, which splits on && | > before bash sees anything. The command is
#    therefore base64-encoded and passed inside ONE double-quoted argument, then decoded by bash on SERVER.
#  - PATH excludes Docker Desktop's resources/bin (home of docker-credential-desktop.exe, which fails outside the
#    interactive logon session); a `docker` shim in D:\agl-docker-config\bin execs docker.exe by full path.
#  - DOCKER_CONFIG is a plain {} config (no credential store; public images only).
#  - cwd = the repository checkout on D:
# Usage: deploy/server/agl-ssh.sh 'docker compose -f stack/docker-compose.yml ps'
set -euo pipefail
SCRIPT="export PATH='/c/Program Files/Git/bin':'/c/Program Files/Git/usr/bin':'/c/Program Files/Git/cmd':/d/agl-docker-config/bin:/c/Windows/System32:/c/Windows   # Git first: System32 has WSL's bash.exe
export DOCKER_CONFIG=/d/agl-docker-config MSYS_NO_PATHCONV=1 HOME=/c/Users/andre
cd /d/Projects/AI-Gov-Layer || exit 97
$*"
B64=$(printf '%s' "$SCRIPT" | base64 | tr -d '\n')
ssh -o BatchMode=yes -o ConnectTimeout=15 server "\"C:\\Program Files\\Git\\bin\\bash.exe\" -c \"echo $B64 | base64 -d | bash\"" 2>&1 | tr -d '\r'
