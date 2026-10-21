"""DLP: secrets and personal data are detected; policy blocks both (owner decision 2026-10-21, PD-49).
Only finding TYPES and COUNTS are ever logged; matched values stay inside the request.

Two kinds of personal-data match are exempt and counted separately, never silently:
  own_identity — the caller's own registered address (developer tools put it in their system prompt);
  test_data    — addresses on domains reserved for examples and tests (RFC 2606, RFC 6761)."""
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

# Reserved for documentation and testing: example.com/.net/.org and their subdomains (RFC 2606),
# and the special-use TLDs .test, .example, .invalid, .localhost (RFC 2606 / RFC 6761). Nobody can own them.
TEST_DOMAINS = ("example.com", "example.net", "example.org")
TEST_TLDS = ("test", "example", "invalid", "localhost")

@dataclass
class Finding:
    type: str
    rule: str
    count: int

@dataclass
class ScanResult:
    secrets: list = field(default_factory=list)
    pii: list = field(default_factory=list)
    exempt: dict = field(default_factory=lambda: {"own_identity": 0, "test_data": 0})
    def summary(self) -> dict:
        return {"secrets": sum(f.count for f in self.secrets), "pii": sum(f.count for f in self.pii),
                "findings": [{"type": f.type, "rule": f.rule, "count": f.count} for f in self.secrets + self.pii],
                "exempt": dict(self.exempt)}

def _iban_ok(s: str) -> bool:
    s = s.replace(" ", "")
    if len(s) < 15:
        return False
    r = s[4:] + s[:4]
    n = "".join(str(int(ch, 36)) for ch in r)
    return int(n) % 97 == 1

def is_test_value(type_: str, value: str) -> bool:
    """Only email addresses have a reserved namespace; phone numbers and IBANs never count as test data."""
    if type_ != "EMAIL":
        return False
    domain = value.rsplit("@", 1)[-1].lower().rstrip(".")
    return any(domain == d or domain.endswith("." + d) for d in TEST_DOMAINS) or domain.rsplit(".", 1)[-1] in TEST_TLDS

def scan(text: str, own_values: tuple | list = ()) -> ScanResult:
    """own_values: the caller's own registered identifiers (today: the identity's email address)."""
    res = ScanResult()
    own = {v.strip().lower() for v in own_values if v}
    for name, rx in SECRET_RULES.items():
        c = len(rx.findall(text))
        if c:
            res.secrets.append(Finding(name, f"secret.{name.lower()}.v1", c))
    for name, rx in PII_RULES.items():
        matches = [m.group(0) for m in rx.finditer(text)]
        if name == "IBAN":
            matches = [m for m in matches if _iban_ok(m)]
        counted = 0
        for m in matches:
            if m.lower() in own:
                res.exempt["own_identity"] += 1
            elif is_test_value(name, m):
                res.exempt["test_data"] += 1
            else:
                counted += 1
        if counted:
            res.pii.append(Finding(name, f"pii.{name.lower()}.v1", counted))
    return res
