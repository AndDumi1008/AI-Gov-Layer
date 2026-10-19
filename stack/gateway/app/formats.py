"""Translate between the OpenAI chat and Anthropic messages surfaces and an internal form; synthesize SSE streams."""
import json, time, uuid

def _text_of(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for b in content:
        if isinstance(b, dict):
            if b.get("type") == "text":
                parts.append(b.get("text", ""))
            elif b.get("type") == "tool_result":
                parts.append(_text_of(b.get("content")))
            elif b.get("type") == "tool_use":
                parts.append(json.dumps(b.get("input", {})))
        elif isinstance(b, str):
            parts.append(b)
    return "\n".join(parts)

def parse_openai(body: dict) -> dict:
    msgs = [{"role": m.get("role", "user"), "content": _text_of(m.get("content"))} for m in body.get("messages", [])]
    system = "\n".join(m["content"] for m in msgs if m["role"] == "system") or None
    msgs = [m for m in msgs if m["role"] != "system"]
    return {"surface": "openai", "model": body.get("model", ""), "system": system, "messages": msgs,
            "max_tokens": int(body.get("max_tokens") or body.get("max_completion_tokens") or 1024), "stream": bool(body.get("stream"))}

def parse_anthropic(body: dict) -> dict:
    msgs = [{"role": m.get("role", "user"), "content": _text_of(m.get("content"))} for m in body.get("messages", [])]
    system = _text_of(body.get("system")) or None
    return {"surface": "anthropic", "model": body.get("model", ""), "system": system, "messages": msgs,
            "max_tokens": int(body.get("max_tokens") or 1024), "stream": bool(body.get("stream"))}

def all_text(req: dict) -> str:
    return "\n".join(([req["system"]] if req.get("system") else []) + [m["content"] for m in req["messages"]])

def apply_text(req: dict, fn) -> dict:
    out = dict(req)
    out["system"] = fn(req["system"]) if req.get("system") else None
    out["messages"] = [{"role": m["role"], "content": fn(m["content"])} for m in req["messages"]]
    return out

# ---- responses
def render_openai(req: dict, text: str, usage: dict, model: str) -> dict:
    return {"id": f"chatcmpl-{uuid.uuid4().hex[:12]}", "object": "chat.completion", "created": int(time.time()), "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": usage["input_tokens"], "completion_tokens": usage["output_tokens"], "total_tokens": usage["input_tokens"] + usage["output_tokens"]}}

def render_anthropic(req: dict, text: str, usage: dict, model: str) -> dict:
    return {"id": f"msg_{uuid.uuid4().hex[:16]}", "type": "message", "role": "assistant", "model": model,
            "content": [{"type": "text", "text": text}], "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"]}}

def sse_openai(resp: dict):
    base = {"id": resp["id"], "object": "chat.completion.chunk", "created": resp["created"], "model": resp["model"]}
    text = resp["choices"][0]["message"]["content"]
    yield "data: " + json.dumps({**base, "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]}) + "\n\n"
    for i in range(0, len(text), 64):
        yield "data: " + json.dumps({**base, "choices": [{"index": 0, "delta": {"content": text[i:i+64]}, "finish_reason": None}]}) + "\n\n"
    yield "data: " + json.dumps({**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}], "usage": resp["usage"]}) + "\n\n"
    yield "data: [DONE]\n\n"

def sse_anthropic(resp: dict):
    def ev(name, data):
        return f"event: {name}\ndata: {json.dumps(data)}\n\n"
    text = resp["content"][0]["text"]
    head = {k: v for k, v in resp.items() if k != "content"}
    head["content"] = []
    head["usage"] = {"input_tokens": resp["usage"]["input_tokens"], "output_tokens": 0}
    yield ev("message_start", {"type": "message_start", "message": head})
    yield ev("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}})
    for i in range(0, len(text), 64):
        yield ev("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text[i:i+64]}})
    yield ev("content_block_stop", {"type": "content_block_stop", "index": 0})
    yield ev("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": resp["usage"]["output_tokens"]}})
    yield ev("message_stop", {"type": "message_stop"})

def error_body(surface: str, status: int, code: str, message: str, event_id: str | None, extra: dict | None = None) -> dict:
    extra = extra or {}
    if surface == "anthropic":
        t = {401: "authentication_error", 402: "permission_error", 403: "permission_error", 404: "not_found_error", 429: "rate_limit_error", 502: "api_error", 503: "overloaded_error"}.get(status, "api_error")
        return {"type": "error", "error": {"type": t, "message": f"[AGL {code}] {message}"}, "agl": {"code": code, "event_id": event_id, **extra}}
    return {"error": {"message": f"[AGL {code}] {message}", "type": "agl_governance", "code": code, "event_id": event_id, **extra}}
