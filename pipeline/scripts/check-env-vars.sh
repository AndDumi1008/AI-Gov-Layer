#!/usr/bin/env bash
# Env-var rules for Gate 1 (see docs/08 §4):
#  1. every variable read in code is declared in .env.example (or config/schema.env)
#  2. no .env file is committed
#  3. secret-like variables have no default value in code
# Exit 1 on any violation. Stack-agnostic: scans common read patterns.
set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# every .env.example in the repo (one per deployable unit) plus an optional config schema
DECL_FILES=(); while IFS= read -r f; do [ -n "$f" ] && DECL_FILES+=("$f"); done < <( (git ls-files --cached --others --exclude-standard 2>/dev/null | grep -E '(^|/)\.env\.example$|(^|/)config/schema\.env$') || find . -name .env.example -not -path '*/node_modules/*')
SRC_GLOBS=(--include='*.js' --include='*.ts' --include='*.tsx' --include='*.py' --include='*.go' --include='*.rb' --include='*.java' --include='*.kt' --include='*.cs' --include='*.php' --include='*.yaml' --include='*.yml' --include='*.toml' --include='*.sh')
EXCLUDES=(--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=vendor --exclude-dir=dist --exclude-dir=build --exclude-dir=.venv)
fail=0

# Rule 2
if git ls-files --error-unmatch .env >/dev/null 2>&1 || [ -f .env ] && git ls-files | grep -qx '.env'; then
  echo "::error::.env is committed to the repository"; fail=1
fi

# Declared variables
declared=$(for f in "${DECL_FILES[@]}"; do [ -f "$f" ] && grep -Eo '^[A-Z][A-Z0-9_]+' "$f"; done | sort -u || true)
if [ -z "$declared" ]; then
  echo "::error::no .env.example (or config/schema.env) found — every variable must be declared"; fail=1
fi

# Variables read in code (common patterns)
# code: explicit environment reads; manifests (yaml/toml/json): ${VAR} interpolation. Shell-local $VARS are not env reads;
# .github/ is excluded because workflow env is declared inside the workflow file itself.
used=$( { grep -rhoE \
  'process\.env\.[A-Z][A-Z0-9_]+|process\.env\[["'"'"'][A-Z][A-Z0-9_]+|os\.environ(\.get)?\(?\[?["'"'"'][A-Z][A-Z0-9_]+|os\.getenv\(["'"'"'][A-Z][A-Z0-9_]+|os\.Getenv\("[A-Z][A-Z0-9_]+|ENV\[["'"'"'][A-Z][A-Z0-9_]+|System\.getenv\("[A-Z][A-Z0-9_]+' \
  "${SRC_GLOBS[@]}" "${EXCLUDES[@]}" . 2>/dev/null; \
  grep -rhoE '\$\{[A-Z][A-Z0-9_]+(:-[^}]*)?\}' --include='*.yaml' --include='*.yml' --include='*.toml' --include='*.json' "${EXCLUDES[@]}" --exclude-dir=.github . 2>/dev/null; } \
  | grep -oE '[A-Z][A-Z0-9_]{2,}' | sort -u || true)

# Rule 1
ignore_re='^(PATH|HOME|USER|SHELL|PWD|TERM|LANG|TZ|CI|GITHUB_[A-Z_]+|RUNNER_[A-Z_]+|NODE_ENV|GOOS|GOARCH|JAVA_HOME)$'
undeclared=$(comm -23 <(echo "$used") <(echo "$declared") | grep -vE "$ignore_re" || true)
if [ -n "$undeclared" ]; then
  echo "::error::variables read in code but not declared in ${DECL_FILES[*]}:"; echo "$undeclared" | sed 's/^/  - /'; fail=1
fi

# Rule 3: secret-like names must not have defaults
secret_re='[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|PASSWD|API_KEY|PRIVATE_KEY|DSN|CONNECTION_STRING)[A-Z0-9_]*'
defaults=$(grep -rnE \
  "(process\.env\.${secret_re}\s*(\|\||\?\?)\s*['\"][^'\"]+['\"])|(os\.environ\.get\(['\"]${secret_re}['\"]\s*,\s*['\"][^'\"]+['\"])|(os\.getenv\(['\"]${secret_re}['\"]\s*,\s*['\"][^'\"]+['\"])" \
  "${SRC_GLOBS[@]}" "${EXCLUDES[@]}" . 2>/dev/null || true)
if [ -n "$defaults" ]; then
  echo "::error::secret-like variables with default values in code (a missing secret must fail at startup):"; echo "$defaults" | sed 's/^/  /'; fail=1
fi

# Also: declared secrets must have placeholder values only in .env.example
for f in "${DECL_FILES[@]}"; do
  [ -f "$f" ] || continue
  if grep -nE "^${secret_re}=.{12,}" "$f" | grep -vEi '(changeme|placeholder|xxx|<.*>|example|dummy|\*\*\*)' ; then
    echo "::error::$f contains a secret-like variable with what looks like a real value"; fail=1
  fi
done

[ $fail -eq 0 ] && echo "env-vars: OK ($(echo "$used" | grep -c . || echo 0) variables used, all declared)"
exit $fail
