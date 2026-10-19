"""Backend adapters. Non-streaming calls; the gateway synthesizes streams for the caller."""
import httpx
from . import config

class BackendError(Exception):
    pass

def _anthropic(req: dict, redacted: dict, model: str) -> dict:
    if not config.ANTHROPIC_API_KEY:
        raise BackendError("ANTHROPIC_API_KEY not configured")
    body = {"model": model, "max_tokens": redacted["max_tokens"], "messages": [{"role": m["role"], "content": m["content"]} for m in redacted["messages"]]}
    if redacted.get("system"):
        body["system"] = redacted["system"]
    with httpx.Client(timeout=120.0) as c:   # trust_env=True: goes through HTTPS_PROXY = egress-proxy
        r = c.post(f"{config.ANTHROPIC_URL}/v1/messages", json=body,
                   headers={"x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    if r.status_code >= 400:
        raise BackendError(f"anthropic {r.status_code}: {r.text[:300]}")
    j = r.json()
    text = "".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text")
    return {"text": text, "input_tokens": j["usage"]["input_tokens"], "output_tokens": j["usage"]["output_tokens"],
            "cached_tokens": j["usage"].get("cache_read_input_tokens", 0) or 0, "provider_request_id": j.get("id"), "model": j.get("model", model)}

def _openai_compatible(base_url: str, req: dict, redacted: dict, model: str) -> dict:
    msgs = ([{"role": "system", "content": redacted["system"]}] if redacted.get("system") else []) + redacted["messages"]
    body = {"model": model, "messages": msgs, "max_tokens": redacted["max_tokens"], "stream": False}
    with httpx.Client(timeout=300.0, trust_env=False) as c:   # internal network, no proxy
        r = c.post(f"{base_url}/v1/chat/completions", json=body)
    if r.status_code >= 400:
        raise BackendError(f"backend {r.status_code}: {r.text[:300]}")
    j = r.json()
    text = j["choices"][0]["message"]["content"] or ""
    u = j.get("usage") or {}
    return {"text": text, "input_tokens": int(u.get("prompt_tokens") or 0), "output_tokens": int(u.get("completion_tokens") or 0),
            "cached_tokens": 0, "provider_request_id": j.get("id"), "model": j.get("model", model)}

def call(endpoint: dict, req: dict, redacted: dict) -> dict:
    """endpoint: registry row (alias, base_url, residency). Resolves the PoC backend from env."""
    alias = endpoint["alias"]
    if alias == config.LOCAL_ALIAS:
        return _openai_compatible(config.LOCAL_BACKEND_URL, req, redacted, config.LOCAL_MODEL if "ollama" in config.LOCAL_BACKEND_URL else "mock-local")
    if config.EXTERNAL_BACKEND == "anthropic":
        return _anthropic(req, redacted, config.ANTHROPIC_MODEL)
    return _openai_compatible(config.MOCK_URL, req, redacted, "mock-external")
