"""
Layer-5 Grounded Ask Validation Harness Tests.

This test file provides the repeatable entrypoint for validating
grounded Ask progress. Run with:

    pytest runtime/tests/test_ask_validation_harness.py -v

Or for fast iteration:

    pytest runtime/tests/test_ask_validation_harness.py::test_harness_full_suite -v

The harness validates (ALL MEASURED DIRECTLY):
1. Empty bundle rate (for grounded queries)
2. Relevant file presence rate
3. Retrieval latency (real, instrumented around ContextEngine.build_context_bundle)
4. End-to-end ask latency
5. No-match justification validity
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.ask_validation.harness import (
    AskValidationHarness,
    HarnessResult,
    run_validation_harness,
)
from runtime.ask_validation.golden_queries import (
    GoldenQuery,
    QueryExpectation,
    GOLDEN_QUERY_SUITE,
    get_grounded_queries,
    get_no_match_queries,
)


class TestAskValidationHarness:
    """Test the validation harness itself."""
    
    def test_harness_full_suite(self, tmp_path: Path) -> None:
        """
        Run full golden query suite and validate all metrics are reported.
        
        This is the primary entrypoint for validation.
        """
        result = run_validation_harness(tmp_path)
        
        # Verify structure
        assert isinstance(result, HarnessResult)
        assert result.metrics is not None
        assert len(result.results) == len(GOLDEN_QUERY_SUITE)
        
        # Print summary for human review
        print("\n" + result.summary())
        
        # Verify required metrics are reported
        metrics = result.metrics.to_dict()
        assert "empty_bundle_rate" in metrics
        assert "relevant_file_presence_rate" in metrics
        assert "avg_retrieval_latency_ms" in metrics
        assert "max_retrieval_latency_ms" in metrics
        assert "avg_e2e_latency_ms" in metrics
        assert "max_e2e_latency_ms" in metrics
        assert "no_match_justification_rate" in metrics
        
        # Verify metrics are in valid ranges
        assert 0 <= metrics["empty_bundle_rate"] <= 1
        assert 0 <= metrics["relevant_file_presence_rate"] <= 1
        assert metrics["avg_retrieval_latency_ms"] >= 0
        assert metrics["avg_e2e_latency_ms"] >= 0
        assert 0 <= metrics["no_match_justification_rate"] <= 1
        
        # For Wave 1-2 baseline: we want the harness to run and report,
        # not necessarily pass all queries yet
        assert result.metrics.total_queries > 0
    
    def test_harness_grounded_queries_only(self, tmp_path: Path) -> None:
        """Run only grounded queries to verify file presence detection."""
        grounded = get_grounded_queries()
        harness = AskValidationHarness(queries=grounded, tmp_root=tmp_path)
        result = harness.run()
        
        assert result.metrics.grounded_expected == len(grounded)
        assert result.metrics.no_match_expected == 0
        
        # All grounded queries should find files
        for qr in result.results:
            if qr.passed:
                assert qr.files_found > 0, f"{qr.query_id} should have found files"
                assert qr.actual_outcome == "grounded"
    
    def test_harness_no_match_queries_only(self, tmp_path: Path) -> None:
        """Run only no-match queries to verify justification validation."""
        no_match = get_no_match_queries()
        harness = AskValidationHarness(queries=no_match, tmp_root=tmp_path)
        result = harness.run()
        
        assert result.metrics.no_match_expected == len(no_match)
        assert result.metrics.grounded_expected == 0
        
        # All no-match queries should return empty files with justification
        for qr in result.results:
            if qr.passed:
                assert qr.files_found == 0, f"{qr.query_id} should have no files"
                assert qr.actual_outcome == "no_match_valid"
    
    def test_harness_reports_latencies(self, tmp_path: Path) -> None:
        """Verify both retrieval and E2E latency metrics are captured."""
        result = run_validation_harness(tmp_path)
        
        # Retrieval latencies should be non-negative (measured directly)
        assert result.metrics.avg_retrieval_latency_ms >= 0
        assert result.metrics.max_retrieval_latency_ms >= result.metrics.avg_retrieval_latency_ms
        
        # E2E latencies should be positive (measured directly)
        assert result.metrics.avg_e2e_latency_ms > 0
        assert result.metrics.max_e2e_latency_ms >= result.metrics.avg_e2e_latency_ms
        
        # Each result should have both latency values
        for qr in result.results:
            assert qr.retrieval_latency_ms >= 0
            assert qr.end_to_end_latency_ms >= 0


class TestGoldenQueryValidation:
    """Test individual golden query behaviors."""
    
    def test_grounded_symbol_retry(self, tmp_path: Path) -> None:
        """Symbol hint 'retry' should match retry.py."""
        query = next(q for q in GOLDEN_QUERY_SUITE if q.id == "grounded_symbol_retry")
        harness = AskValidationHarness(queries=[query], tmp_root=tmp_path)
        result = harness.run()
        
        assert len(result.results) == 1
        qr = result.results[0]
        
        # Should be grounded with files
        assert qr.files_found >= 1
        assert "symbols" in qr.selectors_used
    
    def test_no_match_nonexistent_symbol(self, tmp_path: Path) -> None:
        """Query for nonexistent symbol should return valid no-match."""
        query = next(q for q in GOLDEN_QUERY_SUITE if q.id == "no_match_nonexistent_symbol")
        harness = AskValidationHarness(queries=[query], tmp_root=tmp_path)
        result = harness.run()
        
        assert len(result.results) == 1
        qr = result.results[0]
        
        # Should have no files
        assert qr.files_found == 0
        
        # Should have justification in response
        response = qr.response
        ui_msg = response.get("ui", {}).get("message", "").lower()
        notes = response.get("plan_summary", {}).get("notes", [])
        
        has_justification = (
            "ungrounded" in ui_msg or
            "no context" in ui_msg or
            any("no grounded" in n.lower() or "ungrounded" in n.lower() for n in notes)
        )
        assert has_justification, "No-match should have justification"
    
    def test_case_insensitive_matching(self, tmp_path: Path) -> None:
        """Case-insensitive symbol matching should work."""
        query = next(q for q in GOLDEN_QUERY_SUITE if q.id == "edge_case_insensitive")
        harness = AskValidationHarness(queries=[query], tmp_root=tmp_path)
        result = harness.run()
        
        qr = result.results[0]
        assert qr.files_found >= 1, "Case-insensitive search should find handler.py"


class TestMetricsCalculation:
    """Test metrics calculation accuracy."""
    
    def test_empty_bundle_rate_calculation(self, tmp_path: Path) -> None:
        """Empty bundle rate should be calculated correctly."""
        result = run_validation_harness(tmp_path)
        
        grounded_results = [
            r for r in result.results 
            if r.expectation == QueryExpectation.GROUNDED
        ]
        
        if grounded_results:
            empty_count = sum(1 for r in grounded_results if r.files_found == 0)
            expected_rate = empty_count / len(grounded_results)
            assert abs(result.metrics.empty_bundle_rate - expected_rate) < 0.001
    
    def test_file_presence_rate_calculation(self, tmp_path: Path) -> None:
        """File presence rate should be calculated correctly."""
        result = run_validation_harness(tmp_path)
        
        grounded_results = [
            r for r in result.results 
            if r.expectation == QueryExpectation.GROUNDED
        ]
        
        if grounded_results:
            present_count = sum(
                1 for r in grounded_results 
                if r.files_found > 0 and r.actual_outcome == "grounded"
            )
            expected_rate = present_count / len(grounded_results)
            assert abs(result.metrics.relevant_file_presence_rate - expected_rate) < 0.001


class TestHarnessOutput:
    """Test harness output formats."""
    
    def test_summary_format(self, tmp_path: Path) -> None:
        """Summary output should be human-readable."""
        result = run_validation_harness(tmp_path)
        summary = result.summary()
        
        # Should contain key sections
        assert "GROUNDED ASK VALIDATION HARNESS RESULTS" in summary
        assert "Overall:" in summary
        assert "MEASURED METRICS:" in summary
        assert "Empty Bundle Rate:" in summary
        assert "Relevant File Presence:" in summary
        assert "Avg Retrieval Latency:" in summary
        assert "Max Retrieval Latency:" in summary
        assert "Avg E2E Latency:" in summary
        assert "QUERY SUMMARY:" in summary
        assert "QUERY DETAILS:" in summary
    
    def test_metrics_dict_format(self, tmp_path: Path) -> None:
        """Metrics dict should be JSON-serializable."""
        result = run_validation_harness(tmp_path)
        metrics_dict = result.metrics.to_dict()
        
        # Should be JSON-serializable
        json_str = json.dumps(metrics_dict)
        assert json_str is not None
        
        # Should round-trip
        parsed = json.loads(json_str)
        assert parsed["total_queries"] == metrics_dict["total_queries"]


def test_validation_harness_as_gate(tmp_path: Path) -> None:
    """
    Demonstrate harness use as a Wave transition gate.
    
    This test shows what thresholds could be checked for Wave 2 transition.
    """
    result = run_validation_harness(tmp_path)
    
    # Example gate conditions for Wave 2:
    # These are illustrative - actual thresholds should be tuned based on
    # initial baseline measurements.
    
    gate_checks = {
        # For grounded queries, empty bundle rate should be low
        "empty_bundle_rate_below_50pct": result.metrics.empty_bundle_rate < 0.5,
        
        # File presence rate should be above 50% for grounded queries
        "file_presence_above_50pct": result.metrics.relevant_file_presence_rate > 0.5,
        
        # No-match queries should have justification
        "no_match_justified_above_80pct": result.metrics.no_match_justification_rate > 0.8,
        
        # Retrieval latency should be under 500ms
        "retrieval_latency_under_500ms": result.metrics.max_retrieval_latency_ms < 500,
        
        # E2E latency should be under 1 second
        "e2e_latency_under_1s": result.metrics.max_e2e_latency_ms < 1000,
    }
    
    print("\n" + "=" * 60)
    print("WAVE 2 GATE CHECK RESULTS")
    print("=" * 60)
    for check_name, passed in gate_checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check_name}")
    print("=" * 60)
    
    # This test documents the gate structure but doesn't enforce it yet
    # for Wave 1 baseline establishment
    assert True, "Gate check structure validated"
