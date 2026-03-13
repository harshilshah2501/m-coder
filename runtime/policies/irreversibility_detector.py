"""
Deterministic irreversibility detector — runtime_hardening_v1.1.

Pure rule-based classification. No LLM. No heuristic scoring. Binary output only.
Constitutional guards CODE-01 through CODE-08; detector does not alter constitutional definitions.
"""

from __future__ import annotations

import logging
from typing import Any

DETECTOR_VERSION = "1.1"

# Canonical action_type values that map to required guards (rule-based only).
ACTION_MERGE_PROTECTED = "merge_to_protected_branch"
ACTION_MERGE = "merge"
ACTION_AUTONOMOUS = "autonomous_execution"
ACTION_CONFIG_API = "config_external_api"
ACTION_INFRA_MUTATION = "infra_mutation"
ACTION_INFRA_DEPLOY = "deploy"
ACTION_RUNTIME_STATE = "runtime_state_change"
ACTION_ADAPTIVE_VALIDATION = "adaptive_validation"

PROTECTED_DEPLOYMENT_TARGETS = ("main", "master", "release")
PROTECTED_RESOURCE_SCOPE = "protected_branch"
PRODUCTION_ENVIRONMENTS = ("production", "prod")
PRODUCTION_INFRA_ACTIONS = (ACTION_INFRA_MUTATION, ACTION_INFRA_DEPLOY)

_logger = logging.getLogger(__name__)


def _log_structured(event: str, payload: dict[str, Any]) -> None:
    """Structured logging only; no free text."""
    _logger.info("%s", {"event": event, "version": DETECTOR_VERSION, **payload})


def classify(input_spec: dict[str, Any]) -> dict[str, Any]:
    """
    Classify an action as reversible or irreversible. First matching rule wins.

    Input schema:
        action_type: str
        resource_scope: str
        ownership_context: str
        cross_tenant: bool
        deployment_target: str
        environment: str

    Output schema:
        irreversible: bool
        required_guard: str | None
        requires_HITL: bool
    """
    action_type = input_spec.get("action_type")
    resource_scope = input_spec.get("resource_scope")
    cross_tenant = input_spec.get("cross_tenant") is True
    deployment_target = input_spec.get("deployment_target")
    environment = input_spec.get("environment")

    # Rule order: explicit first, then by guard code.
    # Cross-tenant modification → CODE-07
    if cross_tenant:
        out = {"irreversible": True, "required_guard": "CODE-07", "requires_HITL": True}
        _log_structured("classification", {"irreversible": True, "required_guard": "CODE-07"})
        return out

    # Merge to protected branch → CODE-01
    if action_type == ACTION_MERGE_PROTECTED:
        out = {"irreversible": True, "required_guard": "CODE-01", "requires_HITL": True}
        _log_structured("classification", {"irreversible": True, "required_guard": "CODE-01"})
        return out
    if action_type == ACTION_MERGE and (
        deployment_target in PROTECTED_DEPLOYMENT_TARGETS or resource_scope == PROTECTED_RESOURCE_SCOPE
    ):
        out = {"irreversible": True, "required_guard": "CODE-01", "requires_HITL": True}
        _log_structured("classification", {"irreversible": True, "required_guard": "CODE-01"})
        return out

    # Autonomous execution without human token → CODE-02
    if action_type == ACTION_AUTONOMOUS:
        out = {"irreversible": True, "required_guard": "CODE-02", "requires_HITL": True}
        _log_structured("classification", {"irreversible": True, "required_guard": "CODE-02"})
        return out

    # Config change affecting external API contract → CODE-04
    if action_type == ACTION_CONFIG_API:
        out = {"irreversible": True, "required_guard": "CODE-04", "requires_HITL": True}
        _log_structured("classification", {"irreversible": True, "required_guard": "CODE-04"})
        return out

    # Production infra mutation → CODE-05
    if action_type in PRODUCTION_INFRA_ACTIONS and (
        environment in PRODUCTION_ENVIRONMENTS or deployment_target == "production"
    ):
        out = {"irreversible": True, "required_guard": "CODE-05", "requires_HITL": True}
        _log_structured("classification", {"irreversible": True, "required_guard": "CODE-05"})
        return out

    # Runtime state change without rollback path → CODE-06
    if action_type == ACTION_RUNTIME_STATE:
        out = {"irreversible": True, "required_guard": "CODE-06", "requires_HITL": True}
        _log_structured("classification", {"irreversible": True, "required_guard": "CODE-06"})
        return out

    # Adaptive behavior altering validation policy → CODE-08
    if action_type == ACTION_ADAPTIVE_VALIDATION:
        out = {"irreversible": True, "required_guard": "CODE-08", "requires_HITL": True}
        _log_structured("classification", {"irreversible": True, "required_guard": "CODE-08"})
        return out

    # Default: reversible unless explicitly classified
    out = {"irreversible": False, "required_guard": None, "requires_HITL": False}
    _log_structured("classification", {"irreversible": False, "required_guard": None})
    return out
