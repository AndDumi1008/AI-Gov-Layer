import os

def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)

DATABASE_URL = env("DATABASE_URL", "postgresql://agl_gateway@localhost:5432/postgres")
OPA_URL = env("OPA_URL", "http://localhost:8181")
MINIO_URL = env("MINIO_URL", "http://localhost:9000")
MINIO_USER = env("MINIO_ROOT_USER", "agl-audit")
MINIO_PASSWORD = env("MINIO_ROOT_PASSWORD", "")
ANCHOR_URL = env("ANCHOR_URL", "http://localhost:9010")
ANCHOR_USER = env("ANCHOR_ROOT_USER", "agl-anchor")
ANCHOR_PASSWORD = env("ANCHOR_ROOT_PASSWORD", "")
AUDIT_BUCKET = "agl-audit"
ANCHOR_BUCKET = "agl-anchor"
AUDIT_RETENTION_DAYS = int(env("AUDIT_RETENTION_DAYS", "1"))
SEGMENT_MAX_EVENTS = int(env("AGL_SEGMENT_MAX_EVENTS", "20"))
SEGMENT_MAX_SECONDS = int(env("AGL_SEGMENT_MAX_SECONDS", "60"))

# Content store (PD-50): no default key. Without it every model request fails closed.
CONTENT_KEY = os.environ.get("AGL_CONTENT_KEY")
CONTENT_RETENTION_DAYS = int(env("AGL_CONTENT_RETENTION_DAYS", "30"))

# EU only, no exception (PD-43): the self-hosted tier is the only backend; there is no external provider adapter.
LOCAL_BACKEND_URL = env("AGL_LOCAL_BACKEND_URL", "http://mock-model:8000")
LOCAL_MODEL = env("AGL_LOCAL_MODEL", "qwen2.5-coder:7b")

DEV_ISSUER = env("AGL_DEV_ISSUER", "true").lower() == "true"
ISSUER = "agl-dev-issuer"
AUDIENCE = "agl"
KEYS_DIR = env("AGL_KEYS_DIR", "/keys")
TOKEN_TTL_HOURS = 8
LOCAL_ALIAS = env("AGL_LOCAL_ALIAS", "code-local")
DEFAULT_ALIAS = env("AGL_DEFAULT_ALIAS", LOCAL_ALIAS)
