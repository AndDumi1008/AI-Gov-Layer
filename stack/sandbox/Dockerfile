# Agent sandbox for the PoC: ephemeral, unprivileged, read-only root, no credentials.
# Started by `agl sandbox new <repo>` with: --network agl-net --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 256
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends git make ca-certificates curl python3 python3-pip nodejs npm jq && rm -rf /var/lib/apt/lists/* \
 && useradd -m -u 10001 -s /bin/bash agent
COPY agl-shell /usr/local/bin/agl-shell
RUN chmod +x /usr/local/bin/agl-shell
USER agent
WORKDIR /workspace
ENV HOME=/home/agent AGL_GATEWAY=http://gateway:8000
ENTRYPOINT ["/usr/local/bin/agl-shell"]
