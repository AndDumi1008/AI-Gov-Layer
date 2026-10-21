#!/usr/bin/env python3
"""AGL MCP server (stdio, JSON-RPC 2.0): fire the canaries, read the scoreboard, explain an event, list runs —
from a prompt in any MCP-capable assistant. Vendor-neutral by construction: it speaks only the Model Context
Protocol and the gateway's HTTP API. No dependencies beyond the standard library.

Register with Claude Code:  claude mcp add agl -- python3 /path/to/stack/mcp/agl_mcp.py
Environment: AGL_URL (gateway), AGL_TOKEN or AGL_TOKEN_FILE (~/.agl/token), AGL_CA_FILE (internal CA)."""
import sys, os, json, ssl, pathlib, urllib.request, urllib.error

URL = os.environ.get("AGL_URL", "http://127.0.0.1:4000").rstrip("/")
CA = os.environ.get("AGL_CA_FILE")
CTX = ssl.create_default_context(cafile=CA) if CA else None

def token():
    t = os.environ.get("AGL_TOKEN")
    if t: return t
    p = pathlib.Path(os.environ.get("AGL_TOKEN_FILE", pathlib.Path.home() / ".agl" / "token"))
    return p.read_text().strip() if p.exists() else ""

def call(method, path, body=None):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode() if body is not None else None, method=method)
    req.add_header("content-type", "application/json"); req.add_header("authorization", "Bearer " + token())
    try:
        with urllib.request.urlopen(req, timeout=600, context=CTX) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:500]}

TOOLS = [
    {"name": "run_canaries", "description": "Fire the gateway's canaries (deliberate violations that must be blocked and clean inputs that must pass); results are written to the audit chain. Optional ids, e.g. [\"C-SECRET\",\"C-WORM\"].",
     "inputSchema": {"type": "object", "properties": {"ids": {"type": "array", "items": {"type": "string"}}}}},
    {"name": "list_canaries", "description": "List the available canaries with the guardrail each one proves.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "scoreboard", "description": "Scoreboard of a run, rendered only from the audit chain. Give run_id, or omit for the latest run.",
     "inputSchema": {"type": "object", "properties": {"run_id": {"type": "string"}}}},
    {"name": "explain_event", "description": "Return one audit event with the policy explanation of its reason codes.",
     "inputSchema": {"type": "object", "properties": {"event_id": {"type": "string"}}, "required": ["event_id"]}},
    {"name": "list_runs", "description": "List recent runs (config snapshots).", "inputSchema": {"type": "object", "properties": {}}},
]

def tool(name, args):
    if name == "run_canaries": return call("POST", "/agl/canary/run", {"ids": args.get("ids")})
    if name == "list_canaries": return call("GET", "/agl/canaries")
    if name == "scoreboard":
        rid = args.get("run_id") or (call("GET", "/agl/runs?limit=1").get("runs") or [{}])[0].get("run_id")
        return call("GET", f"/agl/scoreboard/{rid}") if rid else {"error": "no runs"}
    if name == "explain_event": return call("GET", f"/agl/events/{args['event_id']}")
    if name == "list_runs": return call("GET", "/agl/runs")
    return {"error": f"unknown tool {name}"}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: msg = json.loads(line)
        except Exception: continue
        mid, m, p = msg.get("id"), msg.get("method"), msg.get("params") or {}
        if m == "initialize":
            res = {"protocolVersion": p.get("protocolVersion", "2024-11-05"), "capabilities": {"tools": {}}, "serverInfo": {"name": "agl", "version": "0.1"}}
        elif m == "notifications/initialized": continue
        elif m == "tools/list": res = {"tools": TOOLS}
        elif m == "tools/call":
            out = tool(p.get("name"), p.get("arguments") or {})
            res = {"content": [{"type": "text", "text": json.dumps(out, indent=1, default=str)}], "isError": bool(isinstance(out, dict) and out.get("error"))}
        elif m == "ping": res = {}
        else:
            if mid is None: continue
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"unknown method {m}"}}) + "\n"); sys.stdout.flush(); continue
        if mid is not None:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": res}) + "\n"); sys.stdout.flush()

if __name__ == "__main__":
    main()
