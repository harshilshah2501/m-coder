from __future__ import annotations

import os
from pathlib import Path

import pytest

from runtime.layer5.audit.l58_grounded_harness import run_l58_harness


def _require_canonical_root() -> Path:
    _env = os.environ.get("PR6_CANONICAL_ROOT", "").strip()
    if not _env:
        pytest.skip("PR6_CANONICAL_ROOT env var not set; skipping grounded baseline test.")
    root = Path(_env).resolve()
    if not root.is_dir():
        pytest.skip(f"PR6_CANONICAL_ROOT path not found: {root}")
    return root


def test_l58_hardening_slice_pr6_and_target_families() -> None:
    root = _require_canonical_root()
    os.environ["PR6_AIOPS_ROOT"] = str(root)
    os.environ["PR6_CANONICAL_ROOT"] = str(root)

    result = run_l58_harness(
        Path("runtime/layer5/audit/l58_hardening_slice_test_output"),
        suite="full",
        include_generated_perturbations=True,
    )

    # PR-6 baseline must remain locked.
    assert result.pr6.top1_hits == result.pr6.total
    assert result.pr6.top3_hits == result.pr6.total
    assert abs(result.pr6.mean_first_relevant_rank - 1.0) < 1e-9
    assert abs(result.pr6.mean_noise_dominance_top5 - 0.0) < 1e-9

    by_id = {r.case_id: r for r in result.cases}

    ask_plan_prefixes = (
        "l58.ask.topology.where.base",
        "l58.plan.ingestion.impact.base",
    )
    ask_plan_rows = [r for cid, r in by_id.items() if cid.startswith(ask_plan_prefixes)]
    assert ask_plan_rows
    for row in ask_plan_rows:
        assert row.top3_anchor_hit, f"{row.case_id}: top-3 anchor must hold for this slice"
        assert row.first_relevant_rank is not None and row.first_relevant_rank <= 3
        assert row.noise_dominance_top5 <= 0.2

    code_prefix = "l58.code.metrics.parser.target.base"
    code_rows = [r for cid, r in by_id.items() if cid.startswith(code_prefix)]
    assert code_rows
    for row in code_rows:
        # Slice goal: avoid brittle NO_MATCH collapse and keep code-targeting anchors in top-3.
        assert row.predicted_evidence_class != "NO_MATCH", f"{row.case_id}: should not collapse to NO_MATCH"
        assert "evidence_drift" not in row.hard_fail_reasons
        assert row.top3_anchor_hit, f"{row.case_id}: expected code-target anchor in top-3"
        assert row.first_relevant_rank is not None and row.first_relevant_rank <= 3
