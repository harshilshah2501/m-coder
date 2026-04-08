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
    assert "top1_owner_accuracy" in result.drift.metrics
    assert "top3_anchor_hit_rate" in result.drift.metrics
    assert "weak_evidence_precision" in result.drift.metrics
    assert "no_match_honesty_precision" in result.drift.metrics
    owner_cases = [c for c in result.cases if c.must_hit_top1_owner]
    anchor_cases = [c for c in result.cases if c.must_hit_top3_anchor]
    if owner_cases:
        expected_top1 = sum(1 for c in owner_cases if c.top1_owner_match) / len(owner_cases)
        assert abs(result.drift.metrics["top1_owner_accuracy"] - expected_top1) < 1e-9
    if anchor_cases:
        expected_top3 = sum(1 for c in anchor_cases if c.top3_anchor_hit) / len(anchor_cases)
        assert abs(result.drift.metrics["top3_anchor_hit_rate"] - expected_top3) < 1e-9
    if os.environ.get("L58_REQUIRE_PASS") == "1":
        assert result.passed, f"Full gate failed: {result.drift.hard_failures}"
