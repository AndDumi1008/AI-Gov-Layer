"""Dev issuer (stand-in for the corporate IdP) + token verification.
Human tokens: sub=<user>, kind=human. Delegated agent tokens: kind=agent, act={sub}, sandbox, repo, scopes."""
import os, time, uuid, json, base64
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from . import config

_KEY_PATH = os.path.join(config.KEYS_DIR, "issuer.pem")
_private = None
_kid = "agl-dev-1"

def _load_or_create():
    global _private
    if _private:
        return _private
    os.makedirs(config.KEYS_DIR, exist_ok=True)
    if os.path.exists(_KEY_PATH):
        _private = serialization.load_pem_private_key(open(_KEY_PATH, "rb").read(), password=None)
    else:
        _private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with open(_KEY_PATH, "wb") as f:
            f.write(_private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    return _private

def _b64(n: int) -> str:
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def jwks() -> dict:
    pub = _load_or_create().public_key().public_numbers()
    return {"keys": [{"kty": "RSA", "use": "sig", "alg": "RS256", "kid": _kid, "n": _b64(pub.n), "e": _b64(pub.e)}]}

def mint(sub: str, kind: str = "human", ttl_hours: int = config.TOKEN_TTL_HOURS, **extra) -> str:
    now = int(time.time())
    claims = {"iss": config.ISSUER, "aud": config.AUDIENCE, "sub": sub, "kind": kind, "iat": now, "exp": now + ttl_hours * 3600, "jti": uuid.uuid4().hex}
    claims.update({k: v for k, v in extra.items() if v is not None})
    return jwt.encode(claims, _load_or_create(), algorithm="RS256", headers={"kid": _kid})

def verify(token: str) -> dict:
    pub = _load_or_create().public_key()
    return jwt.decode(token, pub, algorithms=["RS256"], audience=config.AUDIENCE, issuer=config.ISSUER)
