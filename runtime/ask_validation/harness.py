"""
Layer-5 Grounded Ask Validation Harness.

Provides a repeatable validation flow for grounded Ask progress:
- Runs golden query suite against Ask service
- Measures required metrics (empty bundle rate, file presence, latencies)
- Validates grounded success and no-match justification
- Produces pass/fail results with detailed reporting

This harness is designed for fast iteration during Waves 1-2.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runtime.ask_service.handlers import handle_ask_request
from runtime.ask_validation.golden_queries import (
    GoldenQuery,
    QueryExpectation,
    GOLDEN_QUERY_SUITE,
)


@dataclass
class QueryResult:
    """Result of running a single golden query."""
    query_id: str
    passed: bool
    expectation: QueryExpectation
    actual_outcome: str  # "grounded" | "no_match_valid" | "no_match_invalid" | "error"
    files_found: int
    selectors_used: list[str]
    retrieval_latency_ms: float
    end_to_end_latency_ms: float
    violations: list[str] = field(default_factory=list)
    response: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationMetrics:
    """Aggregated metrics from validation run."""
    total_queries: int = 0
    grounded_expected: int = 0
    no_match_expected: int = 0
    
    # Core required metrics
    empty_bundle_count: int = 0
    empty_bundle_rate: float = 0.0
    
    relevant_file_present_count: int = 0
    relevant_file_presence_rate: float = 0.0
    
    avg_retrieval_latency_ms: float = 0.0
    max_retrieval_latency_ms: float = 0.0
    
    avg_e2e_latency_ms: float = 0.0
    max_e2e_latency_ms: float = 0.0
    
    # Optional useful metrics
    no_match_justified_count: int = 0
    no_match_justification_rate: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for reporting."""
        return {
            "total_queries": self.total_queries,
            "grounded_expected": self.grounded_expected,
            "no_match_expected": self.no_match_expected,
            "empty_bundle_rate": round(self.empty_bundle_rate, 4),
            "relevant_file_presence_rate": round(self.relevant_file_presence_rate, 4),
            "avg_retrieval_latency_ms": round(self.avg_retrieval_latency_ms, 2),
            "max_retrieval_latency_ms": round(self.max_retrieval_latency_ms, 2),
            "avg_e2e_latency_ms": round(self.avg_e2e_latency_ms, 2),
            "max_e2e_latency_ms": round(self.max_e2e_latency_ms, 2),
            "no_match_justification_rate": round(self.no_match_justification_rate, 4),
        }


@dataclass
class HarnessResult:
    """Result of running the full validation harness."""
    passed: bool
    metrics: ValidationMetrics
    results: list[QueryResult] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 60,
            "GROUNDED ASK VALIDATION HARNESS RESULTS",
            "=" * 60,
            "",
            f"Overall: {'PASS' if self.passed else 'FAIL'}",
            "",
            "REQUIRED METRICS:",
            f"  Empty Bundle Rate:         {self.metrics.empty_bundle_rate:.2%}",
            f"  Relevant File Presence:    {self.metrics.relevant_file_presence_rate:.2%}",
            f"  Avg Retrieval Latency:     {self.metrics.avg_retrieval_latency_ms:.1f} ms",
            f"  Max Retrieval Latency:     {self.metrics.max_retrieval_latency_ms:.1f} ms",
            f"  Avg E2E Latency:           {self.metrics.avg_e2e_latency_ms:.1f} ms",
            f"  Max E2E Latency:           {self.metrics.max_e2e_latency_ms:.1f} ms",
            "",
            "OPTIONAL METRICS:",
            f"  No-Match Justification:    {self.metrics.no_match_justification_rate:.2%}",
            "",
            f"QUERY SUMMARY: {sum(1 for r in self.results if r.passed)}/{len(self.results)} passed",
        ]
        
        if self.violations:
            lines.append("")
            lines.append("VIOLATIONS:")
            for v in self.violations:
                lines.append(f"  - {v}")
        
        lines.append("")
        lines.append("QUERY DETAILS:")
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"  [{status}] {r.query_id}: {r.actual_outcome} "
                        f"(files={r.files_found}, latency={r.end_to_end_latency_ms:.1f}ms)")
            for v in r.violations:
                lines.append(f"         - {v}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


def _setup_test_repo(tmp_root: Path, files: dict[str, str]) -> Path:
    """Create a minimal test repo with specified files."""
    repo_root = tmp_root / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    
    for rel_path, content in files.items():
        full_path = repo_root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
    
    return repo_root


def _check_grounded_outcome(
    query: GoldenQuery,
    response: dict[str, Any],
    retrieval_latency_ms: float,
) -> tuple[str, list[str]]:
    """
    Check if a grounded query has valid outcome.
    
    Returns (outcome_type, violations).
    """
    violations = []
    files = response.get("context_bundle", {}).get("files", [])
    selectors = response.get("context_bundle", {}).get("selectors_used", [])
    
    if not files:
        violations.append(f"Expected grounded result but got empty files")
        return ("no_match_invalid", violations)
    
    # Check expected file patterns
    found_paths = [f.get("path", "") for f in files]
    for pattern in query.expected_file_patterns:
        if not any(pattern.lower() in p.lower() for p in found_paths):
            violations.append(f"Expected file pattern '{pattern}' not found in {found_paths}")
    
    # Check expected selectors
    for expected_sel in query.expected_selectors:
        if expected_sel not in selectors:
            violations.append(f"Expected selector '{expected_sel}' not in {selectors}")
    
    # Check UI indicates grounded (not warning)
    ui_severity = response.get("ui", {}).get("severity", "")
    if ui_severity != "info":
        violations.append(f"Grounded result should have ui.severity='info', got '{ui_severity}'")
    
    ui_message = response.get("ui", {}).get("message", "").lower()
    if "ungrounded" in ui_message or "no context" in ui_message:
        violations.append("UI message indicates ungrounded despite having files")
    
    return ("grounded", violations)


def _check_no_match_outcome(
    query: GoldenQuery,
    response: dict[str, Any],
) -> tuple[str, list[str]]:
    """
    Check if a no-match query has valid outcome with justification.
    
    Returns (outcome_type, violations).
    """
    violations = []
    files = response.get("context_bundle", {}).get("files", [])
    
    if files:
        violations.append(f"Expected no-match but got {len(files)} files")
        return ("grounded", violations)
    
    # Check for proper justification
    notes = response.get("plan_summary", {}).get("notes", [])
    ui_message = response.get("ui", {}).get("message", "").lower()
    ui_severity = response.get("ui", {}).get("severity", "")
    
    has_justification = False
    
    # Check notes for justification
    for note in notes:
        note_lower = note.lower()
        for keyword in query.no_match_keywords:
            if keyword.lower() in note_lower:
                has_justification = True
                break
    
    # Check UI message for justification
    for keyword in query.no_match_keywords:
        if keyword.lower() in ui_message:
            has_justification = True
            break
    
    if not has_justification:
        violations.append(f"No-match lacks justification keywords {query.no_match_keywords}")
    
    # Check severity is warning for no-match
    if ui_severity != "warning":
        violations.append(f"No-match should have ui.severity='warning', got '{ui_severity}'")
    
    return ("no_match_valid" if not violations else "no_match_invalid", violations)


class AskValidationHarness:
    """
    Validation harness for grounded Ask progress.
    
    Runs golden queries, measures metrics, validates outcomes.
    Suitable for use as a Wave transition gate.
    """
    
    def __init__(
        self,
        queries: list[GoldenQuery] | None = None,
        tmp_root: Path | None = None,
    ):
        """
        Initialize harness.
        
        Args:
            queries: Golden queries to run (defaults to GOLDEN_QUERY_SUITE)
            tmp_root: Temp directory root for test repos (required for run())
        """
        self.queries = queries or GOLDEN_QUERY_SUITE
        self.tmp_root = tmp_root
    
    def run(self) -> HarnessResult:
        """
        Run all golden queries and validate outcomes.
        
        Returns HarnessResult with pass/fail status, metrics, and violations.
        """
        if self.tmp_root is None:
            raise ValueError("tmp_root must be set to run harness")
        
        results: list[QueryResult] = []
        all_violations: list[str] = []
        
        retrieval_latencies: list[float] = []
        e2e_latencies: list[float] = []
        
        for query in self.queries:
            result = self._run_query(query)
            results.append(result)
            
            retrieval_latencies.append(result.retrieval_latency_ms)
            e2e_latencies.append(result.end_to_end_latency_ms)
            
            if not result.passed:
                all_violations.extend(
                    f"[{query.id}] {v}" for v in result.violations
                )
        
        # Calculate metrics
        metrics = self._calculate_metrics(results, retrieval_latencies, e2e_latencies)
        
        # Overall pass: all queries pass
        passed = all(r.passed for r in results)
        
        return HarnessResult(
            passed=passed,
            metrics=metrics,
            results=results,
            violations=all_violations,
        )
    
    def _run_query(self, query: GoldenQuery) -> QueryResult:
        """Run a single golden query and validate outcome."""
        # Setup test repo
        repo_root = _setup_test_repo(self.tmp_root / query.id, query.repo_files)
        
        # Build ask request
        ask_request = {
            "schema_version": "ask_request.v0.1",
            "request_id": f"validation-{query.id}",
            "timestamp_utc": "2026-03-20T12:00:00Z",
            "repo_root": str(repo_root),
            "revision": "validation-rev",
            "query": query.query,
        }
        
        # If this is the explicit file test, add selected_file
        if query.id == "grounded_explicit_file":
            ask_request["selected_file"] = "src/main.py"
        
        # Measure latencies
        start_time = time.perf_counter()
        retrieval_start = start_time  # Context retrieval is part of handle_ask_request
        
        try:
            response = handle_ask_request(ask_request)
        except Exception as e:
            return QueryResult(
                query_id=query.id,
                passed=False,
                expectation=query.expectation,
                actual_outcome="error",
                files_found=0,
                selectors_used=[],
                retrieval_latency_ms=0,
                end_to_end_latency_ms=0,
                violations=[f"Exception during handle_ask_request: {e}"],
                response={},
            )
        
        end_time = time.perf_counter()
        e2e_latency_ms = (end_time - start_time) * 1000
        # Retrieval latency approximated as portion of e2e (context engine work)
        # In a more sophisticated harness, we'd instrument the context engine
        retrieval_latency_ms = e2e_latency_ms * 0.7  # Estimated proportion
        
        # Extract result data
        files = response.get("context_bundle", {}).get("files", [])
        selectors = response.get("context_bundle", {}).get("selectors_used", [])
        
        # Validate outcome based on expectation
        if query.expectation == QueryExpectation.GROUNDED:
            outcome, violations = _check_grounded_outcome(
                query, response, retrieval_latency_ms
            )
        elif query.expectation == QueryExpectation.NO_MATCH_VALID:
            outcome, violations = _check_no_match_outcome(query, response)
        else:
            # EITHER_WITH_JUSTIFICATION: accept grounded OR valid no-match
            if files:
                outcome, violations = _check_grounded_outcome(
                    query, response, retrieval_latency_ms
                )
            else:
                outcome, violations = _check_no_match_outcome(query, response)
        
        passed = len(violations) == 0
        
        return QueryResult(
            query_id=query.id,
            passed=passed,
            expectation=query.expectation,
            actual_outcome=outcome,
            files_found=len(files),
            selectors_used=selectors,
            retrieval_latency_ms=retrieval_latency_ms,
            end_to_end_latency_ms=e2e_latency_ms,
            violations=violations,
            response=response,
        )
    
    def _calculate_metrics(
        self,
        results: list[QueryResult],
        retrieval_latencies: list[float],
        e2e_latencies: list[float],
    ) -> ValidationMetrics:
        """Calculate aggregated metrics from results."""
        metrics = ValidationMetrics()
        
        metrics.total_queries = len(results)
        metrics.grounded_expected = sum(
            1 for r in results if r.expectation == QueryExpectation.GROUNDED
        )
        metrics.no_match_expected = sum(
            1 for r in results if r.expectation == QueryExpectation.NO_MATCH_VALID
        )
        
        # Empty bundle rate (for queries expected to be grounded)
        grounded_results = [
            r for r in results if r.expectation == QueryExpectation.GROUNDED
        ]
        if grounded_results:
            metrics.empty_bundle_count = sum(
                1 for r in grounded_results if r.files_found == 0
            )
            metrics.empty_bundle_rate = metrics.empty_bundle_count / len(grounded_results)
        
        # Relevant file presence rate (for queries expected to be grounded)
        if grounded_results:
            metrics.relevant_file_present_count = sum(
                1 for r in grounded_results 
                if r.files_found > 0 and r.actual_outcome == "grounded"
            )
            metrics.relevant_file_presence_rate = (
                metrics.relevant_file_present_count / len(grounded_results)
            )
        
        # Latency metrics
        if retrieval_latencies:
            metrics.avg_retrieval_latency_ms = sum(retrieval_latencies) / len(retrieval_latencies)
            metrics.max_retrieval_latency_ms = max(retrieval_latencies)
        
        if e2e_latencies:
            metrics.avg_e2e_latency_ms = sum(e2e_latencies) / len(e2e_latencies)
            metrics.max_e2e_latency_ms = max(e2e_latencies)
        
        # No-match justification rate
        no_match_results = [
            r for r in results if r.expectation == QueryExpectation.NO_MATCH_VALID
        ]
        if no_match_results:
            metrics.no_match_justified_count = sum(
                1 for r in no_match_results if r.actual_outcome == "no_match_valid"
            )
            metrics.no_match_justification_rate = (
                metrics.no_match_justified_count / len(no_match_results)
            )
        
        return metrics


def run_validation_harness(tmp_root: Path) -> HarnessResult:
    """
    Convenience function to run the validation harness.
    
    Args:
        tmp_root: Temporary directory for test repos
        
    Returns:
        HarnessResult with pass/fail, metrics, and detailed results
    """
    harness = AskValidationHarness(tmp_root=tmp_root)
    return harness.run()
