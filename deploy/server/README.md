# deploy/server — bringing the PoC up on SERVER (Windows 10 Pro, Docker Desktop, WSL 2, GTX 1070)

Order of operations (docs/07 §10.5 and §10.7). Steps marked **(you)** need the Windows administrator or an account login and are done by you; the rest I run from the Mac over Tailscale.

| # | Step | Who | File |
|---|------|-----|------|
| 1 | Tailscale on both machines; SERVER tagged `tag:server` in the admin console (Machines → … → Edit ACL tags); ACL applied. The Mac stays an untagged user device | you | `tailscale-acl.json` |
| 2 | Windows OpenSSH Server enabled; your public key in `administrators_authorized_keys`; firewall rules | you | `windows-setup.ps1`: in an elevated PowerShell run `powershell -ExecutionPolicy Bypass -File .\windows-setup.ps1` (the default execution policy refuses unsigned scripts; the bypass is per invocation) |
| 3 | `.wslconfig` with memory for WSL 2 | you | `wslconfig.ini` → `%UserProfile%\.wslconfig`, then `wsl --shutdown` |
| 4 | Docker Desktop: WSL 2 backend, "Expose daemon" **off**, GPU support on | you | — |
| 5 | Docker context from the Mac; clone the repo on SERVER inside the WSL filesystem | me | `docker-context.sh` |
| 6 | `stack/.env` on SERVER: real passwords, `BIND_IP` = SERVER's Tailscale IP, `SERVER_TS_IP`, `ANTHROPIC_API_KEY` (you type it; I never see it), `AGL_EXTERNAL_BACKEND=anthropic`, `AGL_LOCAL_BACKEND_URL=http://ollama:11434`, `AGL_LOCAL_MODEL=qwen2.5-coder:7b` | you + me | — |
| 7 | Bring up core + model + edge profiles with the GPU overlay; side-load the model weights | me | `Makefile: up-server` + `pull-model.sh` |
| 8 | Tailscale split DNS: `shortandsweet.home.ro → <SERVER Tailscale IP>` | you | admin console |
| 9 | Caddy root certificate into the Mac keychain | you | `trust-ca.sh` prints the steps |
| 10 | Claude Code managed settings on the Mac | you (sudo) | `managed-settings.json` |
| 11 | Run `demo/run-scenarios.sh` from the Mac with `AGL_URL=https://gateway.shortandsweet.home.ro` | me | — |
| 12 | Tier 2: GitHub org + repos, runner container, Supabase stacks | later | `runner/` |

Security posture of the result: only 443 (Caddy) and 22 (SSH) are reachable, and only from the Tailscale range; the governance network has no published ports and no route out except the egress proxy; model weights enter through an explicit pull job, not from inside the stack.

## On SERVER, step by step (WSL 2 shell)

```bash
# inside the WSL distro (Ubuntu), in the Linux filesystem, not /mnt/c
git clone https://github.com/AndDumi1008/AI-Gov-Layer.git ~/AI-Gov-Layer && cd ~/AI-Gov-Layer
cp stack/.env.example stack/.env
# edit stack/.env: BIND_IP=<SERVER Tailscale IP>, SERVER_TS_IP=<same>, real passwords,
#   AGL_EXTERNAL_BACKEND=anthropic, ANTHROPIC_API_KEY=<typed by you>,
#   AGL_LOCAL_BACKEND_URL=http://ollama:11434, AGL_LOCAL_MODEL=qwen2.5-coder:7b
make up-server                          # core + model (GPU overlay) + edge (caddy, coredns)
deploy/server/pull-model.sh             # side-load the weights (one-off container)
docker build -t agl-sandbox:latest stack/sandbox
AGL_URL=http://<SERVER Tailscale IP>:4000 ./demo/run-scenarios.sh    # before DNS/TLS
```

After the Tailscale split-DNS rule and the CA trust on the Mac: `AGL_URL=https://gateway.shortandsweet.home.ro ./demo/run-scenarios.sh` from the Mac.

Docker Desktop on Windows notes: the `gpu` overlay needs "Enable GPU support" in Docker Desktop settings; `make up-server` uses `docker compose -f stack/docker-compose.yml -f stack/docker-compose.gpu.yml`. If the GPU is not available, start without the overlay and the 1.5b model (`AGL_LOCAL_MODEL=qwen2.5-coder:1.5b`) runs on CPU.
