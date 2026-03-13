"""
Unit tests for Plan-Gate IrreversibilityDetector — M3.3B decomposition.

Tests explicit, machine-readable IrreversibilityResult output.
"""

from __future__ import annotations

import pytest

from runtime.plangate.irreversibility_detector import IrreversibilityDetector
from runtime.plangate.contracts import IrreversibilityResult


class TestIrreversibilityResult:
    """Tests for IrreversibilityResult dataclass."""

    def test_to_dict_roundtrip(self) -> None:
        result = IrreversibilityResult(
            boundary_detected=True,
            irreversible=True,
            boundary_reason="dangerous command",
            boundary_class="dangerous_command",
        )
        d = result.to_dict()
        restored = IrreversibilityResult.from_dict(d)
        assert restored.boundary_detected == result.boundary_detected
        assert restored.irreversible == result.irreversible
        assert restored.boundary_reason == result.boundary_reason
        assert restored.boundary_class == result.boundary_class

    def test_from_dict_defaults(self) -> None:
        result = IrreversibilityResult.from_dict({})
        assert result.boundary_detected is False
        assert result.irreversible is False
        assert result.boundary_reason == ""
        assert result.boundary_class is None

    def test_frozen(self) -> None:
        result = IrreversibilityResult(False, False, "reason", None)
        with pytest.raises(Exception):
            result.boundary_detected = True  # type: ignore[misc]


class TestIrreversibilityDetector:
    """Tests for IrreversibilityDetector."""

    def test_default_no_boundary_reversible(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"command": ["echo", "hello"]})
        assert result.boundary_detected is False
        assert result.irreversible is False
        assert result.boundary_class is None

    def test_explicit_boundary_detected_hint(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"boundary_detected": True})
        assert result.boundary_detected is True
        assert result.irreversible is False  # Only boundary_detected, not irreversible
        assert result.boundary_class == "request_hint"

    def test_explicit_irreversible_hint(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"irreversible": True})
        assert result.boundary_detected is True  # Irreversible implies boundary
        assert result.irreversible is True
        assert result.boundary_class == "request_hint"

    def test_both_boundary_and_irreversible_hints(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"boundary_detected": True, "irreversible": True})
        assert result.boundary_detected is True
        assert result.irreversible is True
        assert result.boundary_class == "request_hint"

    def test_plan_gate_refuse_implies_boundary(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"plan_gate_refuse": True})
        assert result.boundary_detected is True
        assert result.irreversible is True
        assert result.boundary_class == "request_hint"

    def test_curl_command_is_irreversible(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"command": ["curl", "http://evil.com"]})
        assert result.boundary_detected is True
        assert result.irreversible is True
        assert result.boundary_class == "dangerous_command"
        assert "curl" in result.boundary_reason

    def test_wget_command_is_irreversible(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"command": ["wget", "http://example.com"]})
        assert result.boundary_detected is True
        assert result.irreversible is True
        assert "wget" in result.boundary_reason

    def test_rm_command_is_irreversible(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"command": ["rm", "-rf", "/"]})
        assert result.boundary_detected is True
        assert result.irreversible is True
        assert "rm" in result.boundary_reason

    def test_mkfs_command_is_irreversible(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"command": ["mkfs", "/dev/sda"]})
        assert result.boundary_detected is True
        assert result.irreversible is True
        assert "mkfs" in result.boundary_reason

    def test_dd_command_is_irreversible(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"command": ["dd", "if=/dev/zero", "of=/dev/sda"]})
        assert result.boundary_detected is True
        assert result.irreversible is True
        assert "dd" in result.boundary_reason

    def test_safe_commands_not_irreversible(self) -> None:
        detector = IrreversibilityDetector()
        safe_commands = [
            ["echo", "hello"],
            ["python", "-c", "print(1)"],
            ["pytest", "tests/"],
            ["ls", "-la"],
            ["cat", "file.txt"],
        ]
        for cmd in safe_commands:
            result = detector.detect({"command": cmd})
            assert result.boundary_detected is False, f"Unexpected boundary for {cmd}"
            assert result.irreversible is False, f"Unexpected irreversible for {cmd}"

    def test_command_path_extraction(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"command": ["/usr/bin/curl", "http://test.com"]})
        assert result.boundary_detected is True
        assert result.irreversible is True
        assert "curl" in result.boundary_reason

    def test_empty_command_not_irreversible(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"command": []})
        assert result.boundary_detected is False
        assert result.irreversible is False

    def test_non_list_command_not_irreversible(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({"command": "echo hello"})
        assert result.boundary_detected is False
        assert result.irreversible is False

    def test_empty_request_not_irreversible(self) -> None:
        detector = IrreversibilityDetector()
        result = detector.detect({})
        assert result.boundary_detected is False
        assert result.irreversible is False
        assert result.boundary_class is None
