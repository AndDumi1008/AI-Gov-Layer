"""Deterministic stand-in for a model: OpenAI- and Anthropic-compatible, echoes what it saw.
/debug/last shows the last prompt received, so the demo can prove the model got placeholders, not PII."""
import time, uuid, json
from fastapi import FastAPI, Request

app = FastAPI()
LAST = {"prompt": None, "ts": None}

def _reply(text: str) -> str:
    return f"[mock-model] I received {len(text)} characters. Echo of what I saw: {text[:400]}"

def _tokens(s: str) -> int:
    return max(1, len(s) // 4)

@app.post("/v1/chat/completions")
async def openai_chat(req: Request):
    body = await req.json()
    prompt = "\n".join(m.get("content", "") if isinstance(m.get("content"), str) else json.dumps(m.get("content")) for m in body.get("messages", []))
    LAST.update(prompt=prompt, ts=time.time())
    out = _reply(prompt)
    return {"id": f"chatcmpl-{uuid.uuid4().hex[:12]}", "object": "chat.completion", "created": int(time.time()),
            "model": body.get("model", "mock"), "choices": [{"index": 0, "message": {"role": "assistant", "content": out}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": _tokens(prompt), "completion_tokens": _tokens(out), "total_tokens": _tokens(prompt) + _tokens(out)}}

@app.post("/v1/messages")
async def anthropic_messages(req: Request):
    body = await req.json()
    parts = []
    if body.get("system"):
        parts.append(body["system"] if isinstance(body["system"], str) else json.dumps(body["system"]))
    for m in body.get("messages", []):
        c = m.get("content")
        parts.append(c if isinstance(c, str) else " ".join(b.get("text", "") for b in c if isinstance(b, dict)))
    prompt = "\n".join(parts)
    LAST.update(prompt=prompt, ts=time.time())
    out = _reply(prompt)
    return {"id": f"msg_{uuid.uuid4().hex[:12]}", "type": "message", "role": "assistant", "model": body.get("model", "mock"),
            "content": [{"type": "text", "text": out}], "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": _tokens(prompt), "output_tokens": _tokens(out)}}

@app.get("/api/tags")
async def tags():
    return {"models": [{"name": "mock"}]}

@app.get("/debug/last")
async def last():
    return LAST

@app.get("/healthz")
async def healthz():
    return {"ok": True}
