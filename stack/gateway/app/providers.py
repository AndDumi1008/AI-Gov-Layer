"""Backend adapters. Non-streaming calls; the gateway synthesizes streams for the caller."""
import httpx
from . import config

class BackendError(Exception):
    pass

def _openai_compatible(base_url: str, req: dict, outbound: dict, model: str) -> dict:
    msgs = ([{"role": "system", "content": outbound["system"]}] if outbound.get("system") else []) + outbound["messages"]
    body = {"model": model, "messages": msgs, "max_tokens": outbound["max_tokens"], "stream": False}
    try:
        with httpx.Client(timeout=300.0, trust_env=False) as c:   # internal network, no proxy
            r = c.post(f"{base_url}/v1/chat/completions", json=body)
    except httpx.HTTPError as e:   # backend down or unreachable: fail closed, the gateway releases the reservation
        raise BackendError(f"backend unreachable: {type(e).__name__}") from e
    if r.status_code >= 400:
        raise BackendError(f"backend {r.status_code}: {r.text[:300]}")
    j = r.json()
    text = j["choices"][0]["message"]["content"] or ""
    u = j.get("usage") or {}
    return {"text": text, "input_tokens": int(u.get("prompt_tokens") or 0), "output_tokens": int(u.get("completion_tokens") or 0),
            "cached_tokens": 0, "provider_request_id": j.get("id"), "model": j.get("model", model)}

def call(endpoint: dict, req: dict, outbound: dict) -> dict:
    """endpoint: registry row (alias, base_url, residency). Resolves the PoC backend from env.
    Only the self-hosted tier has a backend (PD-43); anything else fails even if policy were bypassed."""
    alias = endpoint["alias"]
    if alias == config.LOCAL_ALIAS:
        return _openai_compatible(config.LOCAL_BACKEND_URL, req, outbound, config.LOCAL_MODEL if "ollama" in config.LOCAL_BACKEND_URL else "mock-local")
    raise BackendError(f"no EU backend configured for '{alias}'")
