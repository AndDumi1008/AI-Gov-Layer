# stack/ — AI Governance Layer PoC, Tier 1

Runs on a laptop with Docker (mock model) or on SERVER (Ollama on GPU, Caddy + CoreDNS on the tailnet). Design: [docs/07 §10](../docs/07-poc-requirements.md).

```
make bootstrap        # .env from .env.example, build, start with the mock model
make demo             # scenarios S1–S26 (Tier 1 subset), evidence/ written
make test             # opa tests + gateway unit tests
python3 stack/cli/agl login --as dana && python3 stack/cli/agl ask "hello" -c INTERNAL
```

| Service | Role | Network |
|---------|------|---------|
| `gateway` :4000 | OpenAI (`/v1/chat/completions`) and Anthropic (`/v1/messages`) surfaces; identity → registry → DLP → budget → policy → audit → route | `agl-net` only; outbound through `egress-proxy` |
| `opa` :8181 | policy bundle `policy/` (request decision + agent action decision) | `agl-net` |
| `postgres` :5432 | control plane, ledger, append-only audit hot copy (schema from docs/05 + `schema/002_poc.sql`, seed `010_seed.sql`) | `agl-net` |
| `minio` :9001 console | WORM segments (Object Lock COMPLIANCE) | `agl-net` |
| `minio-anchor` :9011 console | daily anchors, separate credentials | `agl-net` |
| `egress-proxy` | squid allowlist (`api.anthropic.com`); the only container on both `agl-net` and `egress-net` | both |
| `mock-model` (profile mock) | deterministic stand-in; `/debug/last` shows what the model received | `agl-net` |
| `ollama` (profile model) | local open-weight tier = `code-local` | `agl-net` |
| `caddy`, `coredns` (profile edge) | TLS + hostnames on the tailnet | `edge-net` (+ `agl-net` for caddy) |

Seeded identities (dev issuer, `agl login --as <user>`): `dana` developer · `teo` team lead · `mira` budget owner/finance · `ines` security admin · `pawel` DPO · `sven` developer + platform admin (team payments, tiny budget) · `newbie` no training.

Model weights: the in-stack `ollama` has no route to any registry; load weights with `deploy/server/pull-model.sh <model>` (one-off container sharing the volume). Local tier: set `AGL_LOCAL_BACKEND_URL=http://ollama:11434` and start with `--profile model`.

Model aliases: `code-default` (external; `AGL_EXTERNAL_BACKEND=anthropic|mock`, evaluating under a 72 h exception) · `code-local` (self-hosted; CONFIDENTIAL goes here automatically).

Web chat: `https://chat.shortandsweet.home.ro:8443` (or `http://127.0.0.1:4000/chat` locally): connect as a seeded user, see team, roles, training and budget, and get the gateway verdict, model, cost and audit link on every answer.

Claude Code on the Mac: `ANTHROPIC_BASE_URL=https://gateway.shortandsweet.home.ro` (or `http://127.0.0.1:4000` locally) and `ANTHROPIC_AUTH_TOKEN=$(cat ~/.agl/token)`.

Stand-ins and their production replacements are listed in docs/07 §7 and §10.4.
