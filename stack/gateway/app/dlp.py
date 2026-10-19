"""DLP: secrets (block) and personal data (redact) with reversible placeholders.
Only finding TYPES and COUNTS are ever logged; matched values stay inside the request."""
import re
from dataclasses import dataclass, field

SECRET_RULES = {
    "AWS_ACCESS_KEY": re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    "GITHUB_TOKEN": re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
    "ANTHROPIC_KEY": re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b"),
    "OPENAI_KEY": re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
    "PRIVATE_KEY": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "GENERIC_SECRET": re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[A-Za-z0-9/+_\-]{12,}['\"]?"),
    "DB_DSN": re.compile(r"\b(postgres(ql)?|mysql|mongodb(\+srv)?|redis)://[^\s'\"]*:[^\s'\"@]+@[^\s'\"]+"),
}
PII_RULES = {
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "IBAN": re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,4})?\b"),
    "PHONE": re.compile(r"(?<![\w/])(?:\+|00)[1-9]\d{0,2}[ .-]?(?:\(?\d{1,4}\)?[ .-]?){2,4}\d{2,4}\b"),
}

@dataclass
class Finding:
    type: str
    rule: str
    count: int

@dataclass
class ScanResult:
    secrets: list = field(default_factory=list)
    pii: list = field(default_factory=list)
    def summary(self) -> dict:
        return {"secrets": sum(f.count for f in self.secrets), "pii": sum(f.count for f in self.pii),
                "findings": [{"type": f.type, "rule": f.rule, "count": f.count} for f in self.secrets + self.pii]}

def _iban_ok(s: str) -> bool:
    s = s.replace(" ", "")
    if len(s) < 15:
        return False
    r = s[4:] + s[:4]
    n = "".join(str(int(ch, 36)) for ch in r)
    return int(n) % 97 == 1

def scan(text: str) -> ScanResult:
    res = ScanResult()
    for name, rx in SECRET_RULES.items():
        c = len(rx.findall(text))
        if c:
            res.secrets.append(Finding(name, f"secret.{name.lower()}.v1", c))
    for name, rx in PII_RULES.items():
        matches = [m.group(0) for m in rx.finditer(text)]
        if name == "IBAN":
            matches = [m for m in matches if _iban_ok(m)]
        if matches:
            res.pii.append(Finding(name, f"pii.{name.lower()}.v1", len(matches)))
    return res

def redact(text: str, mapping: dict | None = None) -> tuple[str, dict]:
    """Replace PII with [TYPE_n] placeholders; returns new text and placeholder→original map (shared across messages)."""
    mapping = mapping if mapping is not None else {}
    reverse = {v: k for k, v in mapping.items()}
    def repl_factory(t):
        def repl(m):
            val = m.group(0)
            if t == "IBAN" and not _iban_ok(val):
                return val
            if val in reverse:
                return reverse[val]
            n = sum(1 for k in mapping if k.startswith(f"[{t}_")) + 1
            ph = f"[{t}_{n}]"
            mapping[ph] = val
            reverse[val] = ph
            return ph
        return repl
    for t, rx in PII_RULES.items():
        text = rx.sub(repl_factory(t), text)
    return text, mapping

def restore(text: str, mapping: dict) -> str:
    for ph, val in mapping.items():
        text = text.replace(ph, val)
    return text
