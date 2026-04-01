from __future__ import annotations

import os
from pathlib import Path

from runtime.layer5.audit.l58_grounded_harness import run_l58_harness


def test_l58_harness_smoke(tmp_path: Path) -> None:
    result = run_l58_harness(tmp_path, suite="smoke", include_generated_perturbations=True)
    assert result.pr6.total > 0
    assert result.report_json.exists()
    assert result.report_md.exists()
    if result.pr6.hard_failures:
        assert any(x.startswith("pr6_invariant:") for x in result.drift.hard_failures)
    if os.environ.get("L58_REQUIRE_PASS") == "1":
        assert result.passed, f"Smoke gate failed: {result.drift.hard_failures}"


def test_l58_harness_full(tmp_path: Path) -> None:
    result = run_l58_harness(tmp_path, suite="full", include_generated_perturbations=True)
    assert result.cases
    assert result.report_json.exists()
    assert result.report_md.exists()
    assert "owner_drift_rate" in result.drift.metrics
    assert "anchor_drift_rate" in result.drift.metrics
    if os.environ.get("L58_REQUIRE_PASS") == "1":
        assert result.passed, f"Full gate failed: {result.drift.hard_failures}"
