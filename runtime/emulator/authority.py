"""
Deterministic Authority Checker — Runtime Emulator (M3.E0).

Pure rule-based authority validation. No LLM. No inference.
Produces binary AuthorityVerdict (PASS or FAIL).

Invariant: authority_fail NEVER produces safe_execute in downstream routing.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class AuthorityVerdict(str, Enum):
    """Binary authority verdict. No partial/unknown states."""
    PASS = "pass"
    FAIL = "fail"


RISKY_ACTION_TYPES = frozenset({
    "merge_without_approval",
    "commit_prod_change",
    "deploy_production",
    "delete_data",
    "config_change",
    "security_override",
})

REQUIRED_APPROVAL_ACTIONS = frozenset({
    "merge_without_approval",
    "deploy_production",
    "security_override",
})


class AuthorityChecker:
    """
    Deterministic authority checker.
    
    Rules (first match wins):
    1. Missing user_id → FAIL
    2. Missing role → FAIL
    3. Risky action without approval_token → FAIL
    4. Required approval action without approval_chain → FAIL
    5. Default → PASS
    """
    
    def check(
        self,
        user_context: dict[str, Any],
        action_type: str,
    ) -> AuthorityVerdict:
        """
        Check if the action is authorized.
        
        Args:
            user_context: Dict with user_id, role, approval_token, approval_chain
            action_type: The type of action being performed
        
        Returns:
            AuthorityVerdict.PASS or AuthorityVerdict.FAIL
        """
        user_id = user_context.get("user_id")
        if not user_id:
            return AuthorityVerdict.FAIL
        
        role = user_context.get("role")
        if not role:
            return AuthorityVerdict.FAIL
        
        if action_type in RISKY_ACTION_TYPES:
            approval_token = user_context.get("approval_token")
            if not approval_token:
                return AuthorityVerdict.FAIL
        
        if action_type in REQUIRED_APPROVAL_ACTIONS:
            approval_chain = user_context.get("approval_chain") or []
            if not approval_chain:
                return AuthorityVerdict.FAIL
        
        return AuthorityVerdict.PASS
