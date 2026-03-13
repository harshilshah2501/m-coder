"""
Baseline scenario corpus for shadow mode validation (M3.6).

Defines REF, CONF, and DES scenarios used by the shadow runner and harness.
Each scenario produces deterministic plan + decision + ledger when run through PlanGate in shadow mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScenarioDef:
    """Single baseline scenario definition."""
    id: str
    description: str
    expected_phase: str  # REF | CONF | DES
    expected_posture: str  # refuse | bounded_allow | safe_execute
    action_type: str
    user_context: dict[str, Any]
    boundary_phrase: str
    request_id: str
    session_id: str = "sess-shadow"


# Baseline scenario corpus: REF, CONF, DES representative cases
BASELINE_SCENARIOS: list[ScenarioDef] = [
    ScenarioDef(
        id="ref_merge_without_approval",
        description="REF: merge without approval → refuse",
        expected_phase="REF",
        expected_posture="refuse",
        action_type="merge_without_approval",
        user_context={"user_id": "user-123", "role": "developer"},
        boundary_phrase="merge to production branch",
        request_id="req-merge-001",
    ),
    ScenarioDef(
        id="conf_commit_prod_change",
        description="CONF: commit prod change with approval → bounded_allow",
        expected_phase="CONF",
        expected_posture="bounded_allow",
        action_type="commit_prod_change",
        user_context={
            "user_id": "user-456",
            "role": "admin",
            "approval_token": "tok-abc123",
            "approval_chain": ["approver-1", "approver-2"],
        },
        boundary_phrase="commit changes to production config",
        request_id="req-commit-001",
    ),
    ScenarioDef(
        id="des_safe_commit",
        description="DES: safe commit, no boundary → safe_execute",
        expected_phase="DES",
        expected_posture="safe_execute",
        action_type="safe_commit",
        user_context={"user_id": "user-789", "role": "developer"},
        boundary_phrase="",
        request_id="req-safe-001",
    ),
    ScenarioDef(
        id="ref_risky_without_token",
        description="REF: risky action without approval token → refuse",
        expected_phase="REF",
        expected_posture="refuse",
        action_type="merge_without_approval",
        user_context={"user_id": "u1", "role": "admin"},
        boundary_phrase="merge to main",
        request_id="req-ref-002",
    ),
    ScenarioDef(
        id="conf_deploy_intent",
        description="CONF: deploy intent with approval → bounded_allow",
        expected_phase="CONF",
        expected_posture="bounded_allow",
        action_type="deploy_production",
        user_context={
            "user_id": "u2",
            "role": "admin",
            "approval_token": "tok-xyz",
            "approval_chain": ["lead"],
        },
        boundary_phrase="deploy to production environment",
        request_id="req-conf-002",
    ),
]


def scenario_to_event(scenario: ScenarioDef, mode: str = "shadow") -> dict[str, Any]:
    """Convert ScenarioDef to event dict for PlanGate.evaluate_plan."""
    return {
        "action_type": scenario.action_type,
        "user_context": scenario.user_context,
        "boundary_phrase": scenario.boundary_phrase,
        "request_id": scenario.request_id,
        "session_id": scenario.session_id,
        "mode": mode,
    }
