#!/usr/bin/env bash
# Side-load model weights into the stack's Ollama volume using a one-off container on a network WITH internet.
# The in-stack ollama container is on the internal network and cannot (and must not) pull by itself (PD-08).
# Usage: deploy/server/pull-model.sh [model]   (default from stack/.env AGL_LOCAL_MODEL)
set -euo pipefail
cd "$(dirname "$0")/../.."
MODEL="${1:-$(grep -E '^AGL_LOCAL_MODEL=' stack/.env | cut -d= -f2)}"
echo "pulling $MODEL into volume agl_ollama-models"
# the image's entrypoint is the client; a server must run in the same one-off container for `pull`
docker run --rm -v agl_ollama-models:/root/.ollama --entrypoint sh ollama/ollama:0.6.8 -c \
  "ollama serve >/dev/null 2>&1 & for i in \$(seq 1 30); do ollama list >/dev/null 2>&1 && break; sleep 1; done; ollama pull '$MODEL' && ollama show '$MODEL' | head -8"
echo "record the digest in the registry (model.version) before approving the endpoint"
