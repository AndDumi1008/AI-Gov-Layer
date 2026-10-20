#!/usr/bin/env bash
# Run the scenario suite from the Mac against SERVER, then build the evidence report.
# Needs: Tailscale up, split DNS, Caddy root trusted (evidence/agl-root.crt present), docker context "server".
set -euo pipefail
cd "$(dirname "$0")/.."
ENVTMP=$(mktemp); trap 'rm -f "$ENVTMP"' EXIT
scp -q server:D:/Projects/AI-Gov-Layer/stack/.env "$ENVTMP"
export DOCKER_CONTEXT=server
export AGL_URL="${AGL_URL:-https://gateway.shortandsweet.home.ro:8443}"
export AGL_CA_FILE="$PWD/evidence/agl-root.crt"
export AGL_ENV_FILE="$ENVTMP"
export AGL_POLICY_PATH="D:/Projects/AI-Gov-Layer/stack/policy"
if [ "${1:-}" = "--reset" ]; then
  AGL_TOKEN_FILE=/tmp/agl-tok-sven python3 stack/cli/agl login --as sven >/dev/null
  AGL_TOKEN_FILE=/tmp/agl-tok-sven python3 stack/cli/agl demo-reset
fi
./demo/run-scenarios.sh || true
RUN=$(ls -d evidence/run-* | tail -1)
python3 demo/report.py "$RUN" > "$RUN/report.html"
echo "report: $RUN/report.html"
