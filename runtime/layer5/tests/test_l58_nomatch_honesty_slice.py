from __future__ import annotations

import os
from pathlib import Path

import pytest

from runtime.layer5.audit.l58_grounded_harness import run_l58_harness


def _canonical_root() -> Path:
    _env = os.environ.get("PR6_CANONICAL_ROOT", "").strip()
    if not _env:
        pytest.skip("PR6_CANONICAL_ROOT env var not set; skipping grounded baseline test.")
    root = Path(_env).resolve()
    if not root.is_dir():
        pytest.skip(f"PR6_CANONICAL_ROOT path not found: {root}")
    return root


def test_l58_strict_nomatch_case_is_no_match() -> None:
    root = _canonical_root()
    os.environ["PR6_AIOPS_ROOT"] = str(root)
    os.environ["PR6_CANONICAL_ROOT"] = str(root)
    result = run_l58_harness(
        Path("runtime/layer5/audit/l58_nomatch_slice_test_output"),
        suite="full",
        include_generated_perturbations=True,
    )
    row = next(r for r in result.cases if r.case_id == "l58.nomatch.nonexistent.symbol.static")
    assert row.predicted_evidence_class == "NO_MATCH"
    assert row.no_match_honesty_ok
    assert "no_match_honesty_failure" not in row.hard_fail_reasons
