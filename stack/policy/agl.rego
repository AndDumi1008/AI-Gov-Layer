# AI Governance Layer — request policy (PoC bundle). Evaluated by the gateway on every model call.
# Input shape: see docs/02 §2.2 and gateway/app/main.py build_policy_input().
package agl

import rego.v1

rank := {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}

local_alias := data.agl.config.local_alias

# EU only, no exception (PD-43): any other residency, or none, is refused before status or exceptions are read.
eu_residency := {"EU_SELF_HOSTED", "EU_PROVIDER_ZERO_RETENTION", "EU_REGION_HYPERSCALER"}

# ---- hard blocks (any one is enough)
block_reasons contains "NON_EU_ENDPOINT" if not input.model.residency in eu_residency
block_reasons contains "NON_EU_ENDPOINT" if { reroute_needed; input.local_model; not input.local_model.residency in eu_residency }
block_reasons contains "IDENTITY_SUSPENDED" if input.identity.status != "active"
block_reasons contains "TRAINING_REQUIRED" if not input.identity.training_completed
block_reasons contains "DELEGATION_EXPIRED" if { input.identity.kind == "agent"; input.identity.delegation_valid == false }
block_reasons contains "REPO_QUARANTINED" if { input.repo; input.repo.ai_exposure != "allowed" }
block_reasons contains "RESTRICTED_DATA" if input.classification == "RESTRICTED"
block_reasons contains "SECRET_DETECTED" if input.dlp.secrets > 0
block_reasons contains "MODEL_NOT_APPROVED" if { not model_usable }
block_reasons contains "BUDGET_EXHAUSTED" if { input.budget.org; input.budget.org.pct >= 100 }
block_reasons contains "BUDGET_EXHAUSTED" if { input.budget.team; input.budget.team.pct >= 100 }
block_reasons contains "NO_TEAM_BUDGET" if { input.identity.kind != "service"; not input.budget.team }
block_reasons contains "CLASSIFICATION_CEILING" if { not reroute_needed; rank[input.classification] > rank[input.model.ceiling] }
block_reasons contains "CLASSIFICATION_CEILING" if { reroute_needed; rank[input.classification] > rank[input.local_model.ceiling] }
block_reasons contains "LOCAL_MODEL_UNAVAILABLE" if { reroute_needed; not input.local_model }
block_reasons contains "PRODUCTION_CALLER" if input.client.environment == "production"

# A model is usable when approved/restricted, or an EU endpoint evaluating under an active model_enable exception.
model_usable if input.model.status in {"approved", "restricted"}
model_usable if count(exception_applied) > 0

exception_applied contains e.id if { input.model.status == "evaluating"; input.model.residency in eu_residency; some e in input.exceptions; e.type == "model_enable"; e.scope.model_alias == input.model.alias }

# ---- reroute: CONFIDENTIAL never leaves the self-hosted tier
reroute_needed if { input.classification == "CONFIDENTIAL"; input.model.residency != "EU_SELF_HOSTED" }

# ---- soft outcomes
redact_reasons contains "PII_REDACTED" if input.dlp.pii > 0
warn_reasons contains "BUDGET_WARNING" if { input.budget.team; input.budget.team.pct >= 80; input.budget.team.pct < 100 }
warn_reasons contains "BUDGET_WARNING_ORG" if { input.budget.org; input.budget.org.pct >= 80; input.budget.org.pct < 100 }
warn_reasons contains "EXCEPTION_APPLIED" if count(exception_applied) > 0
warn_reasons contains "CLASSIFICATION_REROUTE" if reroute_needed

outcome := "block" if count(block_reasons) > 0
outcome := "reroute" if { count(block_reasons) == 0; reroute_needed }
outcome := "redact" if { count(block_reasons) == 0; not reroute_needed; count(redact_reasons) > 0 }
outcome := "allow" if { count(block_reasons) == 0; not reroute_needed; count(redact_reasons) == 0 }

default log_content := false
log_content if { count(block_reasons) == 0; rank[input.classification] <= rank.INTERNAL }

decision := {
  "outcome": outcome,
  "reasons": sort(array.concat(array.concat([r | some r in block_reasons], [r | some r in redact_reasons]), [r | some r in warn_reasons])),
  "redact": count(redact_reasons) > 0,
  "reroute_to": reroute_to,
  "exception_id": exception_id,
  "obligations": {"log_content": log_content},
}

reroute_to := local_alias if reroute_needed
reroute_to := null if not reroute_needed

exception_id := e if { some e in exception_applied }
exception_id := null if count(exception_applied) == 0

# ---- agent tool-call policy (sandbox hook): allow / deny / require_human

action_deny_reasons contains "DENIED_COMMAND" if { some rx in data.agl.config.denied_patterns; regex.match(rx, input.command) }
action_deny_reasons contains "PATH_OUTSIDE_WORKSPACE" if { regex.match(`(^|\s)rm\s+-[a-zA-Z]*r[a-zA-Z]*\s+(/|~|\$HOME|\.\.)(\s|$)`, input.command) }
action_deny_reasons contains "BINARY_NOT_ALLOWLISTED" if { not binary_allowed }
binary_allowed if { some b in data.agl.config.allowed_binaries; startswith(trim_space(input.command), b) }
action_human if { count(action_deny_reasons) == 0; some rx in data.agl.config.require_human_patterns; regex.match(rx, input.command) }

action := {"outcome": "deny", "reasons": sort([r | some r in action_deny_reasons])} if count(action_deny_reasons) > 0
action := {"outcome": "require_human", "reasons": ["HUMAN_APPROVAL_REQUIRED"]} if { count(action_deny_reasons) == 0; action_human }
action := {"outcome": "allow", "reasons": []} if { count(action_deny_reasons) == 0; not action_human }
