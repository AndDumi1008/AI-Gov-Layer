package agl_test

import rego.v1
import data.agl

base := {
  "identity": {"sub": "dana", "kind": "human", "status": "active", "training_completed": true},
  "classification": "INTERNAL",
  "model": {"alias": "code-default", "status": "approved", "ceiling": "INTERNAL", "residency": "EU_REGION_HYPERSCALER"},
  "local_model": {"alias": "code-local", "status": "approved", "ceiling": "CONFIDENTIAL", "residency": "EU_SELF_HOSTED"},
  "dlp": {"secrets": 0, "pii": 0},
  "budget": {"org": {"pct": 10}, "team": {"pct": 10}},
  "exceptions": [],
  "client": {"type": "cli", "environment": "dev"},
}

test_allow_plain if {
  d := agl.decision with input as base
  d.outcome == "allow"
  d.obligations.log_content == true
}

test_pii_redacts if {
  d := agl.decision with input as object.union(base, {"dlp": {"secrets": 0, "pii": 2}})
  d.outcome == "redact"
  "PII_REDACTED" in d.reasons
}

test_secret_blocks if {
  d := agl.decision with input as object.union(base, {"dlp": {"secrets": 1, "pii": 0}})
  d.outcome == "block"
  "SECRET_DETECTED" in d.reasons
}

test_confidential_reroutes_to_local if {
  d := agl.decision with input as object.union(base, {"classification": "CONFIDENTIAL"})
  d.outcome == "reroute"
  d.reroute_to == "code-local"
  d.obligations.log_content == false
}

test_confidential_on_local_allows if {
  d := agl.decision with input as object.union(base, {"classification": "CONFIDENTIAL", "model": base.local_model})
  d.outcome == "allow"
}

test_restricted_blocks_everywhere if {
  d := agl.decision with input as object.union(base, {"classification": "RESTRICTED", "model": base.local_model})
  d.outcome == "block"
  "RESTRICTED_DATA" in d.reasons
}

test_quarantined_repo_blocks if {
  d := agl.decision with input as object.union(base, {"repo": {"name": "app-x", "ai_exposure": "quarantined"}})
  "REPO_QUARANTINED" in d.reasons
}

test_budget_exhausted_blocks if {
  d := agl.decision with input as object.union(base, {"budget": {"org": {"pct": 10}, "team": {"pct": 100}}})
  "BUDGET_EXHAUSTED" in d.reasons
}

test_org_budget_exhausted_blocks_even_with_team_balance if {
  d := agl.decision with input as object.union(base, {"budget": {"org": {"pct": 100}, "team": {"pct": 5}}})
  "BUDGET_EXHAUSTED" in d.reasons
}

test_budget_warning if {
  d := agl.decision with input as object.union(base, {"budget": {"org": {"pct": 10}, "team": {"pct": 85}}})
  d.outcome == "allow"
  "BUDGET_WARNING" in d.reasons
}

test_evaluating_model_blocked_without_exception if {
  d := agl.decision with input as object.union(base, {"model": {"alias": "code-default", "status": "evaluating", "ceiling": "INTERNAL", "residency": "NON_EU_EVALUATING"}})
  "MODEL_NOT_APPROVED" in d.reasons
}

# An EU endpoint under evaluation may be used under a model_enable exception (F-09).
test_evaluating_eu_model_allowed_with_exception if {
  d := agl.decision with input as object.union(base, {
    "model": {"alias": "code-default", "status": "evaluating", "ceiling": "INTERNAL", "residency": "EU_REGION_HYPERSCALER"},
    "exceptions": [{"id": "exc-1", "type": "model_enable", "scope": {"model_alias": "code-default"}}]})
  d.outcome == "allow"
  d.exception_id == "exc-1"
  "EXCEPTION_APPLIED" in d.reasons
}

# EU only, no exception (PD-43): a non-EU endpoint is refused whatever its status or exceptions.
test_non_eu_endpoint_blocked_even_with_exception if {
  d := agl.decision with input as object.union(base, {
    "model": {"alias": "code-default", "status": "evaluating", "ceiling": "INTERNAL", "residency": "NON_EU_EVALUATING"},
    "exceptions": [{"id": "exc-1", "type": "model_enable", "scope": {"model_alias": "code-default"}}]})
  d.outcome == "block"
  "NON_EU_ENDPOINT" in d.reasons
  not "EXCEPTION_APPLIED" in d.reasons
  d.exception_id == null
}

test_non_eu_endpoint_blocked_even_if_approved if {
  d := agl.decision with input as object.union(base, {"model": {"alias": "us-direct", "status": "approved", "ceiling": "INTERNAL", "residency": "NON_EU_EVALUATING"}})
  d.outcome == "block"
  "NON_EU_ENDPOINT" in d.reasons
}

test_unknown_residency_blocked if {
  d := agl.decision with input as object.union(base, {"model": {"alias": "nobody-knows", "status": "unknown", "ceiling": "PUBLIC", "residency": "none"}})
  "NON_EU_ENDPOINT" in d.reasons
}

test_reroute_target_must_be_eu if {
  d := agl.decision with input as object.union(base, {
    "classification": "CONFIDENTIAL",
    "local_model": {"alias": "code-local", "status": "approved", "ceiling": "CONFIDENTIAL", "residency": "NON_EU_EVALUATING"}})
  d.outcome == "block"
  "NON_EU_ENDPOINT" in d.reasons
}

test_training_required if {
  d := agl.decision with input as object.union(base, {"identity": {"sub": "newbie", "kind": "human", "status": "active", "training_completed": false}})
  "TRAINING_REQUIRED" in d.reasons
}

test_action_kill_denied if {
  a := agl.action with input as {"command": "kill -9 1"}
  a.outcome == "deny"
}

test_action_make_test_allowed if {
  a := agl.action with input as {"command": "make test"}
  a.outcome == "allow"
}

test_action_rm_rf_root_denied if {
  a := agl.action with input as {"command": "rm -rf /"}
  a.outcome == "deny"
}

test_action_git_push_feature_requires_human if {
  a := agl.action with input as {"command": "git push origin feature/x"}
  a.outcome == "require_human"
}

test_action_git_push_main_denied if {
  a := agl.action with input as {"command": "git push origin main"}
  a.outcome == "deny"
}

test_action_unknown_binary_denied if {
  a := agl.action with input as {"command": "nmap 10.0.0.0/8"}
  a.outcome == "deny"
  "BINARY_NOT_ALLOWLISTED" in a.reasons
}
