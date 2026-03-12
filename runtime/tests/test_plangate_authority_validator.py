"""
Unit tests for Plan-Gate AuthorityValidator — M3.3B decomposition.

Tests explicit, machine-readable AuthorityResult output.
"""

from __future__ import annotations

import pytest

from runtime.plangate.authority_validator import AuthorityValidator
from runtime.plangate.contracts import AuthorityResult


class TestAuthorityResult:
    """Tests for AuthorityResult dataclass."""

    def test_to_dict_roundtrip(self) -> None:
        result = AuthorityResult(
            authority_ok=True,
            authority_reason="Granted",
            authority_source="default",
        )
        d = result.to_dict()
        restored = AuthorityResult.from_dict(d)
        assert restored.authority_ok == result.authority_ok
        assert restored.authority_reason == result.authority_reason
        assert restored.authority_source == result.authority_source

    def test_from_dict_defaults(self) -> None:
        result = AuthorityResult.from_dict({})
        assert result.authority_ok is True
        assert result.authority_reason == ""
        assert result.authority_source is None

    def test_frozen(self) -> None:
        result = AuthorityResult(True, "reason", "source")
        with pytest.raises(Exception):
            result.authority_ok = False  # type: ignore[misc]


class TestAuthorityValidator:
    """Tests for AuthorityValidator."""

    def test_default_authority_granted(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"command": ["echo", "hello"]})
        assert result.authority_ok is True
        assert result.authority_source == "default"

    def test_explicit_authority_denied_hint(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"authority_denied": True})
        assert result.authority_ok is False
        assert result.authority_source == "request_hint"
        assert "authority_denied=True" in result.authority_reason

    def test_plan_gate_refuse_implies_authority_denied(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"plan_gate_refuse": True})
        assert result.authority_ok is False
        assert result.authority_source == "request_hint"
        assert "plan_gate_refuse" in result.authority_reason

    def test_curl_command_denies_authority(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"command": ["curl", "http://evil.com"]})
        assert result.authority_ok is False
        assert result.authority_source == "dangerous_command_rule"
        assert "curl" in result.authority_reason

    def test_wget_command_denies_authority(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"command": ["wget", "http://example.com"]})
        assert result.authority_ok is False
        assert "wget" in result.authority_reason

    def test_rm_command_denies_authority(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"command": ["rm", "-rf", "/"]})
        assert result.authority_ok is False
        assert "rm" in result.authority_reason

    def test_mkfs_command_denies_authority(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"command": ["mkfs", "/dev/sda"]})
        assert result.authority_ok is False
        assert "mkfs" in result.authority_reason

    def test_dd_command_denies_authority(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"command": ["dd", "if=/dev/zero", "of=/dev/sda"]})
        assert result.authority_ok is False
        assert "dd" in result.authority_reason

    def test_safe_commands_grant_authority(self) -> None:
        validator = AuthorityValidator()
        safe_commands = [
            ["echo", "hello"],
            ["python", "-c", "print(1)"],
            ["pytest", "tests/"],
            ["ls", "-la"],
            ["cat", "file.txt"],
        ]
        for cmd in safe_commands:
            result = validator.validate({"command": cmd})
            assert result.authority_ok is True, f"Expected authority_ok for {cmd}"

    def test_command_path_extraction(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"command": ["/usr/bin/curl", "http://test.com"]})
        assert result.authority_ok is False
        assert "curl" in result.authority_reason

    def test_empty_command_grants_authority(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"command": []})
        assert result.authority_ok is True

    def test_non_list_command_grants_authority(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({"command": "echo hello"})
        assert result.authority_ok is True

    def test_empty_request_grants_authority(self) -> None:
        validator = AuthorityValidator()
        result = validator.validate({})
        assert result.authority_ok is True
        assert result.authority_source == "default"
