import httpx
from . import config

class GovernanceUnavailable(Exception):
    pass

def decide(inp: dict) -> dict:
    try:
        r = httpx.post(f"{config.OPA_URL}/v1/data/agl/decision", json={"input": inp}, timeout=3.0, trust_env=False)
        r.raise_for_status()
        res = r.json().get("result")
        if not res:
            raise GovernanceUnavailable("policy returned no decision")
        return res
    except (httpx.HTTPError, ValueError) as e:
        raise GovernanceUnavailable(f"policy engine unavailable: {e}") from e

def action(inp: dict) -> dict:
    try:
        r = httpx.post(f"{config.OPA_URL}/v1/data/agl/action", json={"input": inp}, timeout=3.0, trust_env=False)
        r.raise_for_status()
        res = r.json().get("result")
        if not res:
            raise GovernanceUnavailable("policy returned no action decision")
        return res
    except (httpx.HTTPError, ValueError) as e:
        raise GovernanceUnavailable(f"policy engine unavailable: {e}") from e
