from __future__ import annotations

import os
from pathlib import Path

import pytest

from runtime.layer5.audit.pr6_context import (
    PR6_MODE_BASELINE,
    PR6_MODE_FIXTURE,
    PR6_MODE_INVALID,
    classify_pr6_context,
    pr6_fixture_root,
)
from runtime.layer5.tests import test_pr6_closure_baseline_guard as guard_mod


def test_pr6_no_env_skips_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PR6_AIOPS_ROOT", raising=False)
    monkeypatch.delenv("MOTADATA_AIOPS_REPO_ROOT", raising=False)
    with pytest.raises(pytest.skip.Exception):
        guard_mod._resolve_real_repo_root()


def test_pr6_fixture_root_classified_diagnostic() -> None:
    fixture_root = pr6_fixture_root()
    anchors = ("motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java",)
    ctx = classify_pr6_context(fixture_root, anchors, canonical_root=Path("/tmp/canonical-not-fixture"))
    assert ctx.mode == PR6_MODE_FIXTURE


def test_pr6_shifted_fixture_subroot_is_invalid() -> None:
    shifted = pr6_fixture_root() / "motadata"
    anchors = ("motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java",)
    ctx = classify_pr6_context(shifted, anchors, canonical_root=Path("/tmp/canonical-not-fixture"))
    assert ctx.mode == PR6_MODE_INVALID
    assert "shifted-root" in ctx.reason


def test_pr6_canonical_mode_allowed_for_matching_root(tmp_path: Path) -> None:
    root = tmp_path / "canonical"
    anchor = root / "motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java"
    anchor.parent.mkdir(parents=True, exist_ok=True)
    anchor.write_text("class AvailabilityCorrelationEngine {}", encoding="utf-8")
    ctx = classify_pr6_context(
        root,
        ("motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java",),
        canonical_root=root,
    )
    assert ctx.mode == PR6_MODE_BASELINE


def test_pr6_guard_refuses_fixture_root_in_baseline_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PR6_AIOPS_ROOT", str(pr6_fixture_root()))
    monkeypatch.delenv("MOTADATA_AIOPS_REPO_ROOT", raising=False)
    monkeypatch.setenv("PR6_CANONICAL_ROOT", "/home/harshil/Projects/Motadata")
    with pytest.raises(pytest.fail.Exception, match="refused non-baseline context"):
        guard_mod._resolve_real_repo_root()
