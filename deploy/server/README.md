# deploy/server — bringing the PoC up on SERVER (Windows 10 Pro, Docker Desktop, WSL 2, GTX 1070)

Order of operations (docs/07 §10.5 and §10.7). Steps marked **(you)** need the Windows administrator or an account login and are done by you; the rest I run from the Mac over Tailscale.

| # | Step | Who | File |
|---|------|-----|------|
| 1 | Tailscale on both machines; SERVER tagged `tag:server` in the admin console (Machines → … → Edit ACL tags); ACL applied. The Mac stays an untagged user device. If you add `tests`, their `src` must be a concrete user login or device, not an autogroup | you | `tailscale-acl.json` |
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

## On SERVER, step by step (as found on 2026-10-20)

SERVER has no Ubuntu distro: the only WSL 2 distro is Docker Desktop's own. The repository therefore lives on the Windows filesystem at `D:\Projects\AI-Gov-Layer`, Git Bash (`C:\Program Files\Git\bin\bash.exe`) runs the shell scripts, and the `.gitattributes` in the repository forces LF line endings so the scripts work inside containers. Bind mounts from `D:\` work through Docker Desktop.

1. **Docker Desktop must be running in your Windows session.** It cannot be started from SSH. Start it from the Start menu and, in Settings → General, tick "Start Docker Desktop when you sign in". In Settings → Resources → WSL integration nothing extra is needed; GPU support is automatic with the WSL 2 backend and current NVIDIA drivers.
2. `stack\.env` was generated with random passwords and the Tailscale addresses. Add your Anthropic key and switch the external tier on, in an elevated or normal PowerShell:

```powershell
notepad D:\Projects\AI-Gov-Layer\stack\.env     # set ANTHROPIC_API_KEY=... and AGL_EXTERNAL_BACKEND=anthropic
```

3. The rest is driven from the Mac over SSH (or from Git Bash on SERVER):

```bash
# from the Mac
ssh server 'cd /d D:\Projects\AI-Gov-Layer && "C:\Program Files\Git\bin\bash.exe" stack/bootstrap.sh --profile model --profile edge'
ssh server 'cd /d D:\Projects\AI-Gov-Layer && "C:\Program Files\Git\bin\bash.exe" deploy/server/pull-model.sh'
ssh server 'cd /d D:\Projects\AI-Gov-Layer && docker build -t agl-sandbox:latest stack/sandbox'
AGL_URL=http://100.109.138.14:4000 ./demo/run-scenarios.sh       # before DNS/TLS; run on the Mac
```

The GPU overlay (`docker-compose.gpu.yml`) is added by `make up-server`; with Git Bash and no `make`, pass it explicitly: `docker compose -f stack/docker-compose.yml -f stack/docker-compose.gpu.yml --profile model --profile edge up -d --build`.

After the Tailscale split-DNS rule and the CA trust on the Mac: `AGL_URL=https://gateway.shortandsweet.home.ro:8443 ./demo/run-scenarios.sh` from the Mac. Port 8443 because `tailscaled` on SERVER holds 443 for Tailscale Serve (another project); set `AGL_HTTPS_PORT=443` in `stack/.env` if that is ever reset.

Note on GPUs: SERVER reports a GTX 1070 (8 GB) and a GTX 1050 (2 GB). The compose overlay reserves one GPU; Docker picks the first. If the 1050 is chosen, set `device_ids: ["0"]` (or the 1070's UUID from `nvidia-smi -L`) in `docker-compose.gpu.yml`.
