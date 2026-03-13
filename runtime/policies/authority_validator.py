"""
Deterministic authority validator — runtime_hardening_v1.1.

Rule-based enforcement only. No LLM. No fuzzy logic. No substring matching.
Enumerated reason codes only. Binary authorized decision.
Does not alter constitutional definitions.
"""

from __future__ import annotations

import logging
from typing import Any

AUTH_VALIDATOR_VERSION = "1.1"

# Enumerated reason codes only (exact string match in rules).
REASON_USER_ID_MISSING = "USER_ID_MISSING"
REASON_CROSS_TENANT_NO_TOKEN = "CROSS_TENANT_NO_TOKEN"
REASON_CROSS_TENANT_ADMIN_REQUIRED = "CROSS_TENANT_ADMIN_REQUIRED"
REASON_PROTECTED_BRANCH_NO_TOKEN = "PROTECTED_BRANCH_NO_TOKEN"
REASON_PRODUCTION_NO_TOKEN = "PRODUCTION_NO_TOKEN"
REASON_ROLE_NOT_ALLOWED = "ROLE_NOT_ALLOWED"
REASON_APPROVAL_CHAIN_EMPTY = "APPROVAL_CHAIN_EMPTY"

# Exact-match sets only (no substring). Aligned with irreversibility_detector.
PROTECTED_BRANCHES = ("main", "master", "release")
PRODUCTION_ENVS = ("production", "prod")
ALLOWED_ROLES = ("admin", "approver", "operator")
# High-risk set matches irreversibility detector action types (classification/enforcement symmetry).
HIGH_RISK_ACTION_TYPES = (
    "merge_to_protected_branch",
    "merge",
    "autonomous_execution",
    "config_external_api",
    "infra_mutation",
    "deploy",
    "runtime_state_change",
    "adaptive_validation",
)

_logger = logging.getLogger(__name__)


def _log_structured(event: str, payload: dict[str, Any]) -> None:
    """Structured logging only; no free text."""
    _logger.info("%s", {"event": event, "version": AUTH_VALIDATOR_VERSION, **payload})


def validate(input_spec: dict[str, Any]) -> dict[str, Any]:
    """
    Determine if the action is authorized. First matching deny rule wins.

    Input schema:
        user_id: str
        user_role: str
        repo: str
        branch: str
        action_type: str
        resource_scope: str
        cross_tenant: bool
        environment: str
        escalation_token: str | None
        approval_chain: list[str]

    Output schema:
        authorized: bool
        reason_code: str | None
        requires_escalation: bool
    """
    user_id = input_spec.get("user_id")
    user_role = input_spec.get("user_role")
    branch = input_spec.get("branch")
    cross_tenant = input_spec.get("cross_tenant") is True
    environment = input_spec.get("environment")
    escalation_token = input_spec.get("escalation_token")
    approval_chain = input_spec.get("approval_chain")
    action_type = input_spec.get("action_type")

    has_token = escalation_token is not None and escalation_token != ""

    # Rule 1: user_id missing
    if user_id is None or user_id == "":
        out = {"authorized": False, "reason_code": REASON_USER_ID_MISSING, "requires_escalation": False}
        _log_structured("validation", {"authorized": False, "reason_code": REASON_USER_ID_MISSING})
        return out

    # Rule 2: cross_tenant requires escalation token AND user_role == "admin"
    if cross_tenant and not has_token:
        out = {"authorized": False, "reason_code": REASON_CROSS_TENANT_NO_TOKEN, "requires_escalation": True}
        _log_structured("validation", {"authorized": False, "reason_code": REASON_CROSS_TENANT_NO_TOKEN})
        return out
    if cross_tenant and has_token and user_role != "admin":
        out = {"authorized": False, "reason_code": REASON_CROSS_TENANT_ADMIN_REQUIRED, "requires_escalation": True}
        _log_structured("validation", {"authorized": False, "reason_code": REASON_CROSS_TENANT_ADMIN_REQUIRED})
        return out

    # Rule 3: protected branch without escalation token
    if branch in PROTECTED_BRANCHES and not has_token:
        out = {"authorized": False, "reason_code": REASON_PROTECTED_BRANCH_NO_TOKEN, "requires_escalation": True}
        _log_structured("validation", {"authorized": False, "reason_code": REASON_PROTECTED_BRANCH_NO_TOKEN})
        return out

    # Rule 4: production environment without escalation token
    if environment in PRODUCTION_ENVS and not has_token:
        out = {"authorized": False, "reason_code": REASON_PRODUCTION_NO_TOKEN, "requires_escalation": True}
        _log_structured("validation", {"authorized": False, "reason_code": REASON_PRODUCTION_NO_TOKEN})
        return out

    # Rule 5: user_role not in allowed set (exact match only)
    if user_role not in ALLOWED_ROLES:
        out = {"authorized": False, "reason_code": REASON_ROLE_NOT_ALLOWED, "requires_escalation": False}
        _log_structured("validation", {"authorized": False, "reason_code": REASON_ROLE_NOT_ALLOWED})
        return out

    # Rule 6: high-risk action_type with empty approval_chain
    if action_type in HIGH_RISK_ACTION_TYPES and (approval_chain is None or approval_chain == []):
        out = {"authorized": False, "reason_code": REASON_APPROVAL_CHAIN_EMPTY, "requires_escalation": True}
        _log_structured("validation", {"authorized": False, "reason_code": REASON_APPROVAL_CHAIN_EMPTY})
        return out

    # Default: authorized
    out = {"authorized": True, "reason_code": None, "requires_escalation": False}
    _log_structured("validation", {"authorized": True, "reason_code": None})
    return out
