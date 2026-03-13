"""
Unit tests for irreversibility detector — 100% branch coverage.

Pure rule-based; no LLM; binary output only. Constitutional guards CODE-01 through CODE-08.
"""

from __future__ import annotations

import logging
import unittest
from unittest.mock import patch

from runtime.policies.irreversibility_detector import (
    DETECTOR_VERSION,
    classify,
)


def _input(
    action_type: str = "",
    resource_scope: str = "",
    ownership_context: str = "",
    cross_tenant: bool = False,
    deployment_target: str = "",
    environment: str = "",
) -> dict:
    return {
        "action_type": action_type,
        "resource_scope": resource_scope,
        "ownership_context": ownership_context,
        "cross_tenant": cross_tenant,
        "deployment_target": deployment_target,
        "environment": environment,
    }


class TestIrreversibilityDetector(unittest.TestCase):
    """100% branch coverage for irreversibility_detector.classify."""

    # --- CODE-07: Cross-tenant modification ---

    def test_cross_tenant_irreversible_code07(self) -> None:
        out = classify(_input(cross_tenant=True))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-07")
        self.assertTrue(out["requires_HITL"])

    def test_cross_tenant_false_does_not_trigger_code07(self) -> None:
        out = classify(_input(cross_tenant=False, action_type="other"))
        self.assertFalse(out["irreversible"])
        self.assertIsNone(out["required_guard"])

    # --- CODE-01: Merge to protected branch ---

    def test_merge_to_protected_branch_action_code01(self) -> None:
        out = classify(_input(action_type="merge_to_protected_branch"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-01")
        self.assertTrue(out["requires_HITL"])

    def test_merge_with_deployment_target_main_code01(self) -> None:
        out = classify(_input(action_type="merge", deployment_target="main"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-01")

    def test_merge_with_deployment_target_master_code01(self) -> None:
        out = classify(_input(action_type="merge", deployment_target="master"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-01")

    def test_merge_with_deployment_target_release_code01(self) -> None:
        out = classify(_input(action_type="merge", deployment_target="release"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-01")

    def test_merge_with_resource_scope_protected_branch_code01(self) -> None:
        out = classify(_input(action_type="merge", resource_scope="protected_branch"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-01")

    def test_merge_without_protected_target_or_scope_reversible(self) -> None:
        out = classify(_input(action_type="merge", deployment_target="develop", resource_scope="feature"))
        self.assertFalse(out["irreversible"])
        self.assertIsNone(out["required_guard"])
        self.assertFalse(out["requires_HITL"])

    # --- CODE-02: Autonomous execution ---

    def test_autonomous_execution_code02(self) -> None:
        out = classify(_input(action_type="autonomous_execution"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-02")
        self.assertTrue(out["requires_HITL"])

    # --- CODE-04: Config external API ---

    def test_config_external_api_code04(self) -> None:
        out = classify(_input(action_type="config_external_api"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-04")
        self.assertTrue(out["requires_HITL"])

    # --- CODE-05: Production infra mutation ---

    def test_infra_mutation_production_environment_code05(self) -> None:
        out = classify(_input(action_type="infra_mutation", environment="production"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-05")
        self.assertTrue(out["requires_HITL"])

    def test_infra_mutation_prod_environment_code05(self) -> None:
        out = classify(_input(action_type="infra_mutation", environment="prod"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-05")

    def test_infra_mutation_deployment_target_production_code05(self) -> None:
        out = classify(_input(action_type="infra_mutation", deployment_target="production"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-05")

    def test_deploy_production_environment_code05(self) -> None:
        out = classify(_input(action_type="deploy", environment="production"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-05")

    def test_infra_mutation_staging_reversible(self) -> None:
        out = classify(_input(action_type="infra_mutation", environment="staging", deployment_target="staging"))
        self.assertFalse(out["irreversible"])
        self.assertIsNone(out["required_guard"])

    # --- CODE-06: Runtime state change ---

    def test_runtime_state_change_code06(self) -> None:
        out = classify(_input(action_type="runtime_state_change"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-06")
        self.assertTrue(out["requires_HITL"])

    # --- CODE-08: Adaptive validation ---

    def test_adaptive_validation_code08(self) -> None:
        out = classify(_input(action_type="adaptive_validation"))
        self.assertTrue(out["irreversible"])
        self.assertEqual(out["required_guard"], "CODE-08")
        self.assertTrue(out["requires_HITL"])

    # --- Default: reversible ---

    def test_unknown_action_type_reversible(self) -> None:
        out = classify(_input(action_type="read_only"))
        self.assertFalse(out["irreversible"])
        self.assertIsNone(out["required_guard"])
        self.assertFalse(out["requires_HITL"])

    def test_empty_action_type_reversible(self) -> None:
        out = classify(_input(action_type=""))
        self.assertFalse(out["irreversible"])
        self.assertIsNone(out["required_guard"])

    def test_minimal_input_reversible(self) -> None:
        out = classify(_input())
        self.assertFalse(out["irreversible"])
        self.assertIsNone(out["required_guard"])
        self.assertFalse(out["requires_HITL"])

    def test_empty_dict_reversible(self) -> None:
        """Covers input_spec.get() returning None for missing keys; defaults to reversible."""
        out = classify({})
        self.assertFalse(out["irreversible"])
        self.assertIsNone(out["required_guard"])
        self.assertFalse(out["requires_HITL"])

    # --- Output schema ---

    def test_output_schema_keys(self) -> None:
        out = classify(_input(cross_tenant=True))
        self.assertEqual(set(out.keys()), {"irreversible", "required_guard", "requires_HITL"})
        self.assertIsInstance(out["irreversible"], bool)
        self.assertTrue(out["required_guard"] is None or isinstance(out["required_guard"], str))
        self.assertIsInstance(out["requires_HITL"], bool)

    def test_reversible_output_required_guard_null(self) -> None:
        out = classify(_input(action_type="query"))
        self.assertIsNone(out["required_guard"])

    # --- Version ---

    def test_detector_version(self) -> None:
        self.assertEqual(DETECTOR_VERSION, "1.1")

    # --- Structured logging (no free text) ---

    def test_classify_logs_structured(self) -> None:
        with patch.object(
            logging.getLogger("runtime.policies.irreversibility_detector"),
            "info",
        ) as mock_info:
            classify(_input(cross_tenant=True))
            mock_info.assert_called_once()
            # _logger.info("%s", dict) -> call_args[0] = (format_str, payload_dict)
            args = mock_info.call_args[0]
            arg = args[1]
            self.assertIsInstance(arg, dict)
            self.assertIn("event", arg)
            self.assertIn("version", arg)
            self.assertEqual(arg.get("version"), "1.1")
            self.assertIn("irreversible", arg)
            self.assertIn("required_guard", arg)
            self.assertIsInstance(arg.get("event"), str)

    def test_classify_logs_reversible_structured(self) -> None:
        with patch.object(
            logging.getLogger("runtime.policies.irreversibility_detector"),
            "info",
        ) as mock_info:
            classify(_input(action_type="read"))
            mock_info.assert_called_once()
            args = mock_info.call_args[0]
            arg = args[1]
            self.assertIsInstance(arg, dict)
            self.assertFalse(arg["irreversible"])
            self.assertIsNone(arg["required_guard"])


if __name__ == "__main__":
    unittest.main()
