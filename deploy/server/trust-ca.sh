#!/usr/bin/env bash
# Export Caddy's internal root CA from SERVER and print how to trust it on the Mac.
set -euo pipefail
docker --context server cp agl-caddy-1:/data/caddy/pki/authorities/local/root.crt ./agl-root.crt
echo "Root CA saved to ./agl-root.crt. Trust it on the Mac (needs your password):"
echo "  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ./agl-root.crt"
