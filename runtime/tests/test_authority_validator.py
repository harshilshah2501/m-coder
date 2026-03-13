"""
Unit tests for authority validator — 100% branch coverage.

Deterministic rule-based; no LLM; no fuzzy logic; enumerated reason codes only.
"""

from __future__ import annotations

import logging
import unittest
from unittest.mock import patch

from runtime.policies.authority_validator import (
    AUTH_VALIDATOR_VERSION,
    REASON_APPROVAL_CHAIN_EMPTY,
    REASON_CROSS_TENANT_ADMIN_REQUIRED,
    REASON_CROSS_TENANT_NO_TOKEN,
    REASON_PRODUCTION_NO_TOKEN,
    REASON_PROTECTED_BRANCH_NO_TOKEN,
    REASON_ROLE_NOT_ALLOWED,
    REASON_USER_ID_MISSING,
    validate,
)


def _input(
    user_id: str = "u1",
    user_role: str = "admin",
    repo: str = "r",
    branch: str = "develop",
    action_type: str = "read",
    resource_scope: str = "",
    cross_tenant: bool = False,
    environment: str = "staging",
    escalation_token: str | None = None,
    approval_chain: list[str] | None = None,
) -> dict:
    return {
        "user_id": user_id,
        "user_role": user_role,
        "repo": repo,
        "branch": branch,
        "action_type": action_type,
        "resource_scope": resource_scope,
        "cross_tenant": cross_tenant,
        "environment": environment,
        "escalation_token": escalation_token,
        "approval_chain": approval_chain if approval_chain is not None else [],
    }


class TestAuthorityValidator(unittest.TestCase):
    """100% branch coverage for authority_validator.validate."""

    # --- USER_ID_MISSING ---

    def test_user_id_none_not_authorized(self) -> None:
        out = validate(_input(user_id=None))
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_USER_ID_MISSING)
        self.assertFalse(out["requires_escalation"])

    def test_user_id_empty_not_authorized(self) -> None:
        out = validate(_input(user_id=""))
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_USER_ID_MISSING)

    # --- CROSS_TENANT_NO_TOKEN ---

    def test_cross_tenant_no_token_not_authorized(self) -> None:
        out = validate(_input(cross_tenant=True, escalation_token=None))
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_CROSS_TENANT_NO_TOKEN)
        self.assertTrue(out["requires_escalation"])

    def test_cross_tenant_empty_token_not_authorized(self) -> None:
        out = validate(_input(cross_tenant=True, escalation_token=""))
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_CROSS_TENANT_NO_TOKEN)

    def test_cross_tenant_with_token_admin_passes(self) -> None:
        out = validate(
            _input(
                cross_tenant=True,
                escalation_token="t",
                branch="develop",
                environment="staging",
                user_role="admin",
                action_type="read",
                approval_chain=[],
            )
        )
        self.assertTrue(out["authorized"])
        self.assertIsNone(out["reason_code"])
        self.assertFalse(out["requires_escalation"])

    def test_cross_tenant_with_token_developer_not_authorized(self) -> None:
        out = validate(
            _input(
                cross_tenant=True,
                escalation_token="t",
                user_role="developer",
                branch="develop",
                environment="staging",
                approval_chain=[],
            )
        )
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_CROSS_TENANT_ADMIN_REQUIRED)
        self.assertTrue(out["requires_escalation"])

    def test_cross_tenant_with_token_operator_not_authorized(self) -> None:
        out = validate(
            _input(
                cross_tenant=True,
                escalation_token="t",
                user_role="operator",
                branch="develop",
                environment="staging",
                action_type="read",
                approval_chain=[],
            )
        )
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_CROSS_TENANT_ADMIN_REQUIRED)

    # --- PROTECTED_BRANCH_NO_TOKEN ---

    def test_protected_branch_main_no_token_not_authorized(self) -> None:
        out = validate(_input(branch="main", escalation_token=None, cross_tenant=False))
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_PROTECTED_BRANCH_NO_TOKEN)
        self.assertTrue(out["requires_escalation"])

    def test_protected_branch_master_no_token_not_authorized(self) -> None:
        out = validate(_input(branch="master", escalation_token=None, cross_tenant=False))
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_PROTECTED_BRANCH_NO_TOKEN)

    def test_protected_branch_main_with_token_passes(self) -> None:
        out = validate(
            _input(
                branch="main",
                escalation_token="t",
                environment="staging",
                user_role="admin",
                action_type="read",
                approval_chain=[],
            )
        )
        self.assertTrue(out["authorized"])

    def test_protected_branch_release_no_token_not_authorized(self) -> None:
        out = validate(
            _input(
                branch="release",
                escalation_token=None,
                cross_tenant=False,
                environment="staging",
                user_role="admin",
                action_type="read",
                approval_chain=[],
            )
        )
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_PROTECTED_BRANCH_NO_TOKEN)
        self.assertTrue(out["requires_escalation"])

    def test_protected_branch_release_with_token_passes(self) -> None:
        out = validate(
            _input(
                branch="release",
                escalation_token="t",
                cross_tenant=False,
                environment="staging",
                user_role="admin",
                action_type="read",
                approval_chain=[],
            )
        )
        self.assertTrue(out["authorized"])

    # --- PRODUCTION_NO_TOKEN ---

    def test_production_env_no_token_not_authorized(self) -> None:
        out = validate(
            _input(
                branch="develop",
                environment="production",
                escalation_token=None,
                cross_tenant=False,
            )
        )
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_PRODUCTION_NO_TOKEN)
        self.assertTrue(out["requires_escalation"])

    def test_production_prod_env_no_token_not_authorized(self) -> None:
        out = validate(_input(environment="prod", escalation_token=None, cross_tenant=False, branch="develop"))
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_PRODUCTION_NO_TOKEN)

    def test_production_with_token_passes(self) -> None:
        out = validate(
            _input(
                environment="production",
                escalation_token="t",
                branch="develop",
                user_role="admin",
                action_type="read",
                approval_chain=[],
            )
        )
        self.assertTrue(out["authorized"])

    def test_environment_staging_passes_production_rule(self) -> None:
        out = validate(_input(environment="staging", escalation_token=None, branch="develop", user_role="admin", action_type="read", approval_chain=[]))
        self.assertTrue(out["authorized"])

    # --- ROLE_NOT_ALLOWED ---

    def test_role_not_allowed_guest(self) -> None:
        out = validate(
            _input(
                user_role="guest",
                branch="develop",
                environment="staging",
                escalation_token=None,
                cross_tenant=False,
                approval_chain=[],
            )
        )
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_ROLE_NOT_ALLOWED)
        self.assertFalse(out["requires_escalation"])

    def test_role_not_allowed_developer(self) -> None:
        out = validate(_input(user_role="developer", branch="develop", environment="staging", approval_chain=[]))
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_ROLE_NOT_ALLOWED)

    def test_role_not_allowed_none(self) -> None:
        out = validate(_input(user_role=None, branch="develop", environment="staging", approval_chain=[]))
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_ROLE_NOT_ALLOWED)

    def test_role_admin_authorized(self) -> None:
        out = validate(_input(user_role="admin", branch="develop", environment="staging", action_type="read", approval_chain=[]))
        self.assertTrue(out["authorized"])

    def test_role_approver_authorized(self) -> None:
        out = validate(_input(user_role="approver", branch="develop", environment="staging", action_type="read", approval_chain=[]))
        self.assertTrue(out["authorized"])

    def test_role_operator_authorized(self) -> None:
        out = validate(_input(user_role="operator", branch="develop", environment="staging", action_type="read", approval_chain=[]))
        self.assertTrue(out["authorized"])

    # --- APPROVAL_CHAIN_EMPTY ---

    def test_approval_chain_empty_high_risk_not_authorized(self) -> None:
        out = validate(
            _input(
                action_type="merge_to_protected_branch",
                approval_chain=[],
                user_role="admin",
                branch="develop",
                environment="staging",
                escalation_token="t",
            )
        )
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_APPROVAL_CHAIN_EMPTY)
        self.assertTrue(out["requires_escalation"])

    def test_approval_chain_none_high_risk_not_authorized(self) -> None:
        spec = _input(action_type="infra_mutation", user_role="admin", branch="develop", environment="staging", escalation_token="t")
        spec["approval_chain"] = None
        out = validate(spec)
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_APPROVAL_CHAIN_EMPTY)

    def test_approval_chain_non_empty_high_risk_authorized(self) -> None:
        out = validate(
            _input(
                action_type="merge_to_protected_branch",
                approval_chain=["approver1"],
                user_role="admin",
                branch="develop",
                environment="staging",
                escalation_token="t",
            )
        )
        self.assertTrue(out["authorized"])
        self.assertIsNone(out["reason_code"])

    def test_low_risk_action_empty_approval_authorized(self) -> None:
        out = validate(_input(action_type="read", approval_chain=[], user_role="admin", branch="develop", environment="staging"))
        self.assertTrue(out["authorized"])

    def test_high_risk_deploy_empty_chain_not_authorized(self) -> None:
        out = validate(
            _input(
                action_type="deploy",
                approval_chain=[],
                user_role="admin",
                branch="develop",
                environment="staging",
                escalation_token="t",
            )
        )
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_APPROVAL_CHAIN_EMPTY)

    def test_high_risk_autonomous_execution_empty_chain_not_authorized(self) -> None:
        out = validate(
            _input(
                action_type="autonomous_execution",
                approval_chain=[],
                user_role="admin",
                branch="develop",
                environment="staging",
                escalation_token="t",
            )
        )
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_APPROVAL_CHAIN_EMPTY)

    # --- Default authorized ---

    def test_full_authorized_all_rules_pass(self) -> None:
        out = validate(
            _input(
                user_id="u1",
                user_role="admin",
                branch="develop",
                environment="staging",
                cross_tenant=False,
                escalation_token=None,
                action_type="read",
                approval_chain=[],
            )
        )
        self.assertTrue(out["authorized"])
        self.assertIsNone(out["reason_code"])
        self.assertFalse(out["requires_escalation"])

    def test_empty_dict_user_id_missing(self) -> None:
        out = validate({})
        self.assertFalse(out["authorized"])
        self.assertEqual(out["reason_code"], REASON_USER_ID_MISSING)

    # --- Output schema ---

    def test_output_schema_keys(self) -> None:
        out = validate(_input(cross_tenant=True))
        self.assertEqual(set(out.keys()), {"authorized", "reason_code", "requires_escalation"})
        self.assertIsInstance(out["authorized"], bool)
        self.assertTrue(out["reason_code"] is None or isinstance(out["reason_code"], str))
        self.assertIsInstance(out["requires_escalation"], bool)

    def test_authorized_output_reason_code_none(self) -> None:
        out = validate(_input())
        self.assertIsNone(out["reason_code"])

    # --- requires_escalation ---

    def test_requires_escalation_true_cross_tenant(self) -> None:
        out = validate(_input(cross_tenant=True))
        self.assertTrue(out["requires_escalation"])

    def test_requires_escalation_true_protected_branch(self) -> None:
        out = validate(_input(branch="main", cross_tenant=False))
        self.assertTrue(out["requires_escalation"])

    def test_requires_escalation_true_production(self) -> None:
        out = validate(_input(environment="production", branch="develop", cross_tenant=False))
        self.assertTrue(out["requires_escalation"])

    def test_requires_escalation_true_approval_chain_empty(self) -> None:
        out = validate(
            _input(
                action_type="config_external_api",
                approval_chain=[],
                user_role="admin",
                branch="develop",
                environment="staging",
                escalation_token="t",
            )
        )
        self.assertTrue(out["requires_escalation"])

    # --- Version ---

    def test_version_constant(self) -> None:
        self.assertEqual(AUTH_VALIDATOR_VERSION, "1.1")

    # --- Structured logging ---

    def test_structured_logging_deny(self) -> None:
        with patch.object(
            logging.getLogger("runtime.policies.authority_validator"),
            "info",
        ) as mock_info:
            validate(_input(user_id=None))
            mock_info.assert_called_once()
            args = mock_info.call_args[0]
            arg = args[1]
            self.assertIsInstance(arg, dict)
            self.assertIn("event", arg)
            self.assertEqual(arg.get("version"), "1.1")
            self.assertFalse(arg.get("authorized"))
            self.assertEqual(arg.get("reason_code"), REASON_USER_ID_MISSING)

    def test_structured_logging_allow(self) -> None:
        with patch.object(
            logging.getLogger("runtime.policies.authority_validator"),
            "info",
        ) as mock_info:
            validate(_input())
            mock_info.assert_called_once()
            args = mock_info.call_args[0]
            arg = args[1]
            self.assertTrue(arg.get("authorized"))
            self.assertIsNone(arg.get("reason_code"))


if __name__ == "__main__":
    unittest.main()
