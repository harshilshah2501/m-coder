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

from runtime.ask_service.handlers import handle_ask_request, _extract_symbol_hints
from runtime.context.contracts import ContextRequest
from runtime.context.engine import ContextEngine, ContextEngineError, MissingExplicitFilesError
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
from runtime.layer5.retrieval.quality_gate import assess_evidence_quality
from runtime.layer5.workspace.identity import WorkspaceIdentity
from runtime.ask_validation.golden_queries import (
    GoldenQuery,
    GOLDEN_QUERY_SUITE,
    QueryExpectation,
)

MIN_CORE_CODE_PCT_FOR_CODE_INTENT = 0.60
MAX_FALSE_STRONG_RATE = 0.0
MIN_WEAK_CORRECTNESS_RATE = 0.80
MIN_NO_MATCH_CORRECTNESS_RATE = 0.95

# Layer-5 lexical top-k used for dominance metrics (PR-4: measured retrieval, not ContextEngine bundle).
HARNESS_LEXICAL_TOP_K = 8


@dataclass(frozen=True)
class ClosureThresholds:
    min_core_code_pct_for_code_intent: float = MIN_CORE_CODE_PCT_FOR_CODE_INTENT
    max_false_strong_rate: float = MAX_FALSE_STRONG_RATE
    min_weak_correctness_rate: float = MIN_WEAK_CORRECTNESS_RATE
    min_no_match_correctness_rate: float = MIN_NO_MATCH_CORRECTNESS_RATE

@dataclass
class QueryResult:
    """Result of running a single golden query."""
    query_id: str
    passed: bool
    expectation: QueryExpectation
    actual_outcome: str  # "grounded" | "no_match_valid" | "no_match_invalid" | "error"
    files_found: int
    selectors_used: list[str]
    retrieval_latency_ms: float  # Real, measured retrieval latency (ContextEngine)
    end_to_end_latency_ms: float  # Full ask handler latency
    suite: str
    expected_intent_type: str
    expected_quality_set: list[str]
    expected_core_presence: bool
    expected_subsystem: str | None
    query_text: str
    intent_type: str = ""
    evidence_quality: str = ""
    quality_reasons: list[str] = field(default_factory=list)
    dominance_metrics: dict[str, float] = field(default_factory=dict)
    expected_behavior_pass: bool = False
    false_strong: bool = False
    weak_correct: bool = False
    no_match_correct: bool = False
    ambiguity_false_confidence: bool = False
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
    
    # Retrieval latency: INSTRUMENTED
    # Measured directly around ContextEngine.build_context_bundle() call.
    avg_retrieval_latency_ms: float = 0.0
    max_retrieval_latency_ms: float = 0.0
    
    avg_e2e_latency_ms: float = 0.0
    max_e2e_latency_ms: float = 0.0
    
    # Optional useful metrics
    no_match_justified_count: int = 0
    no_match_justification_rate: float = 0.0

    # Dominance metrics
    core_code_pct_top_k: float = 0.0
    code_pct_top_k: float = 0.0
    noise_pct_top_k: float = 0.0

    # Outcome distribution
    strong_rate: float = 0.0
    weak_rate: float = 0.0
    insufficient_rate: float = 0.0
    no_match_rate: float = 0.0

    # Truthfulness metrics
    false_strong_rate: float = 0.0
    weak_correctness_rate: float = 0.0
    no_match_correctness_rate: float = 0.0
    ambiguity_false_confidence_rate: float = 0.0

    # Grouped and threshold summary
    grouped_summary: dict[str, dict[str, Any]] = field(default_factory=dict)
    threshold_results: dict[str, bool] = field(default_factory=dict)
    
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
            "core_code_pct_top_k": round(self.core_code_pct_top_k, 4),
            "code_pct_top_k": round(self.code_pct_top_k, 4),
            "noise_pct_top_k": round(self.noise_pct_top_k, 4),
            "strong_rate": round(self.strong_rate, 4),
            "weak_rate": round(self.weak_rate, 4),
            "insufficient_rate": round(self.insufficient_rate, 4),
            "no_match_rate": round(self.no_match_rate, 4),
            "false_strong_rate": round(self.false_strong_rate, 4),
            "weak_correctness_rate": round(self.weak_correctness_rate, 4),
            "no_match_correctness_rate": round(self.no_match_correctness_rate, 4),
            "ambiguity_false_confidence_rate": round(self.ambiguity_false_confidence_rate, 4),
            "grouped_summary": self.grouped_summary,
            "threshold_results": self.threshold_results,
        }


@dataclass
class HarnessResult:
    """Result of running the full validation harness."""
    passed: bool
    metrics: ValidationMetrics
    results: list[QueryResult] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    closure_thresholds: ClosureThresholds = field(default_factory=ClosureThresholds)
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 60,
            "GROUNDED ASK VALIDATION HARNESS RESULTS",
            "=" * 60,
            "",
            f"Overall: {'PASS' if self.passed else 'FAIL'}",
            "",
            "MEASURED METRICS:",
            f"  Empty Bundle Rate:         {self.metrics.empty_bundle_rate:.2%}",
            f"  Relevant File Presence:    {self.metrics.relevant_file_presence_rate:.2%}",
            f"  Avg Retrieval Latency:     {self.metrics.avg_retrieval_latency_ms:.2f} ms",
            f"  Max Retrieval Latency:     {self.metrics.max_retrieval_latency_ms:.2f} ms",
            f"  Avg E2E Latency:           {self.metrics.avg_e2e_latency_ms:.2f} ms",
            f"  Max E2E Latency:           {self.metrics.max_e2e_latency_ms:.2f} ms",
            "",
            "OPTIONAL METRICS:",
            f"  No-Match Justification:    {self.metrics.no_match_justification_rate:.2%}",
            f"  Core Code % (top-k):       {self.metrics.core_code_pct_top_k:.2%}",
            f"  Code % (top-k):            {self.metrics.code_pct_top_k:.2%}",
            f"  Noise % (top-k):           {self.metrics.noise_pct_top_k:.2%}",
            f"  STRONG rate:               {self.metrics.strong_rate:.2%}",
            f"  WEAK rate:                 {self.metrics.weak_rate:.2%}",
            f"  INSUFFICIENT rate:         {self.metrics.insufficient_rate:.2%}",
            f"  NO_MATCH rate:             {self.metrics.no_match_rate:.2%}",
            f"  False STRONG rate:         {self.metrics.false_strong_rate:.2%}",
            f"  WEAK correctness rate:     {self.metrics.weak_correctness_rate:.2%}",
            f"  NO_MATCH correctness rate: {self.metrics.no_match_correctness_rate:.2%}",
            f"  Ambiguity false-confidence:{self.metrics.ambiguity_false_confidence_rate:.2%}",
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
                        f"(files={r.files_found}, retrieval={r.retrieval_latency_ms:.2f}ms, e2e={r.end_to_end_latency_ms:.2f}ms)")
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
        thresholds: ClosureThresholds | None = None,
    ):
        """
        Initialize harness.
        
        Args:
            queries: Golden queries to run (defaults to GOLDEN_QUERY_SUITE)
            tmp_root: Temp directory root for test repos (required for run())
        """
        self.queries = queries or GOLDEN_QUERY_SUITE
        self.tmp_root = tmp_root
        self.thresholds = thresholds or ClosureThresholds()
    
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
        
        threshold_results = self._evaluate_thresholds(metrics)
        metrics.threshold_results = threshold_results

        return HarnessResult(
            passed=passed,
            metrics=metrics,
            results=results,
            violations=all_violations,
            closure_thresholds=self.thresholds,
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
        selected_file = None
        if query.id == "grounded_explicit_file":
            selected_file = "src/main.py"
            ask_request["selected_file"] = selected_file
        
        # ===================================================================
        # INSTRUMENTED RETRIEVAL TIMING
        # ===================================================================
        # We measure retrieval latency SEPARATELY by calling ContextEngine
        # directly with the same parameters that handle_ask_request would use.
        # This gives us the REAL retrieval path timing.
        # ===================================================================
        
        symbol_hints = _extract_symbol_hints(query.query)
        files_list: list[str] = [selected_file] if selected_file else []
        
        ctx_request = ContextRequest(
            task_id=f"validation-{query.id}",
            revision="validation-rev",
            root_path=str(repo_root),
            files=files_list,
            symbol_hints=symbol_hints,
        )
        
        engine = ContextEngine()
        retrieval_latency_ms = 0.0
        
        # Measure retrieval latency (ContextEngine.build_context_bundle)
        retrieval_start = time.perf_counter()
        try:
            _ = engine.build_context_bundle(ctx_request)
            retrieval_end = time.perf_counter()
            retrieval_latency_ms = (retrieval_end - retrieval_start) * 1000
        except (ContextEngineError, MissingExplicitFilesError):
            retrieval_end = time.perf_counter()
            retrieval_latency_ms = (retrieval_end - retrieval_start) * 1000
        
        # ===================================================================
        # END-TO-END TIMING
        # ===================================================================
        # Now measure full ask handler latency (includes retrieval + planning)
        # ===================================================================
        
        e2e_start = time.perf_counter()
        
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
                retrieval_latency_ms=retrieval_latency_ms,
                end_to_end_latency_ms=0,
                violations=[f"Exception during handle_ask_request: {e}"],
                response={},
            )
        
        e2e_end = time.perf_counter()
        e2e_latency_ms = (e2e_end - e2e_start) * 1000
        
        # Extract result data
        files = response.get("context_bundle", {}).get("files", [])
        selectors = response.get("context_bundle", {}).get("selectors_used", [])
        metadata = response.get("metadata") or {}
        intent_type = str(metadata.get("intent_type") or "")
        evidence_quality = str(metadata.get("evidence_quality") or "")
        quality_reasons = [str(x) for x in (metadata.get("quality_reasons") or [])]
        # Dominance metrics from Layer-5 lexical retrieval (same paths quality_gate uses downstream).
        root_s = str(repo_root.resolve())
        identity = WorkspaceIdentity(
            canonical_root=root_s,
            identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
            original_input=root_s,
            path_type="posix",
            is_git_repo=False,
        )
        idx = build_file_index(identity)
        lex_cfg = LexicalRetrievalConfig()
        lex_ret = retrieve_lexical(idx, query.query, top_k=HARNESS_LEXICAL_TOP_K, config=lex_cfg)
        lexical_paths = [h.relative_path for h in lex_ret.hits]
        layer5_assess = assess_evidence_quality(query.query, lexical_paths)
        dominance_metrics = {k: float(v) for k, v in layer5_assess.dominance_metrics.items()}
        
        # Validate outcome based on expectation
        if query.expectation == QueryExpectation.GROUNDED:
            outcome, violations = _check_grounded_outcome(query, response)
        elif query.expectation == QueryExpectation.NO_MATCH_VALID:
            outcome, violations = _check_no_match_outcome(query, response)
        else:
            # EITHER_WITH_JUSTIFICATION: accept grounded OR valid no-match
            if files:
                outcome, violations = _check_grounded_outcome(query, response)
            else:
                outcome, violations = _check_no_match_outcome(query, response)
        
        passed = len(violations) == 0
        expected_behavior_pass = (
            intent_type == query.expected_intent_type and evidence_quality in set(query.expected_quality_set)
        )
        if query.expected_core_presence and dominance_metrics.get("core_code_in_top_k_pct", 0.0) <= 0:
            expected_behavior_pass = False
            violations.append("Expected core code presence in top-k but got none")

        false_strong = (
            evidence_quality == "STRONG"
            and (
                dominance_metrics.get("noise_in_top_k_pct", 0.0) > 0.5
                or (query.expected_core_presence and dominance_metrics.get("core_code_in_top_k_pct", 0.0) == 0.0)
            )
        )
        weak_correct = evidence_quality == "WEAK" and "STRONG" not in set(query.expected_quality_set)
        # Semantics: NO_MATCH_VALID fixtures list allowed evidence_quality values (e.g. strict NO_MATCH-only
        # vs WEAK/INSUFFICIENT when generic empty/no-grounding is acceptable).
        no_match_correct = (
            query.expectation == QueryExpectation.NO_MATCH_VALID
            and evidence_quality in set(query.expected_quality_set)
        )
        ambiguity_false_confidence = query.suite == "adversarial" and evidence_quality == "STRONG"
        
        return QueryResult(
            query_id=query.id,
            passed=passed,
            expectation=query.expectation,
            actual_outcome=outcome,
            files_found=len(files),
            selectors_used=selectors,
            retrieval_latency_ms=retrieval_latency_ms,
            end_to_end_latency_ms=e2e_latency_ms,
            suite=query.suite,
            expected_intent_type=query.expected_intent_type,
            expected_quality_set=list(query.expected_quality_set),
            expected_core_presence=query.expected_core_presence,
            expected_subsystem=query.expected_subsystem,
            query_text=query.query,
            intent_type=intent_type,
            evidence_quality=evidence_quality,
            quality_reasons=quality_reasons,
            dominance_metrics=dominance_metrics,
            expected_behavior_pass=expected_behavior_pass,
            false_strong=false_strong,
            weak_correct=weak_correct,
            no_match_correct=no_match_correct,
            ambiguity_false_confidence=ambiguity_false_confidence,
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
        
        # Retrieval latency metrics (INSTRUMENTED - measured directly)
        if retrieval_latencies:
            metrics.avg_retrieval_latency_ms = sum(retrieval_latencies) / len(retrieval_latencies)
            metrics.max_retrieval_latency_ms = max(retrieval_latencies)
        
        # E2E latency metrics (measured directly)
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

        # Dominance averages over all results with metadata.
        dom_rows = [r.dominance_metrics for r in results if r.dominance_metrics]
        if dom_rows:
            metrics.core_code_pct_top_k = sum(d.get("core_code_in_top_k_pct", 0.0) for d in dom_rows) / len(dom_rows)
            metrics.code_pct_top_k = sum(d.get("code_in_top_k_pct", 0.0) for d in dom_rows) / len(dom_rows)
            metrics.noise_pct_top_k = sum(d.get("noise_in_top_k_pct", 0.0) for d in dom_rows) / len(dom_rows)

        # Outcome distribution.
        if results:
            metrics.strong_rate = sum(1 for r in results if r.evidence_quality == "STRONG") / len(results)
            metrics.weak_rate = sum(1 for r in results if r.evidence_quality == "WEAK") / len(results)
            metrics.insufficient_rate = sum(1 for r in results if r.evidence_quality == "INSUFFICIENT") / len(results)
            metrics.no_match_rate = sum(1 for r in results if r.evidence_quality == "NO_MATCH") / len(results)

        # Truthfulness metrics.
        if results:
            metrics.false_strong_rate = sum(1 for r in results if r.false_strong) / len(results)
            weak_rows = [r for r in results if r.evidence_quality == "WEAK"]
            metrics.weak_correctness_rate = (
                sum(1 for r in weak_rows if r.expected_behavior_pass) / len(weak_rows)
                if weak_rows
                else 1.0
            )
            no_match_rows = [r for r in results if r.expectation == QueryExpectation.NO_MATCH_VALID]
            metrics.no_match_correctness_rate = (
                sum(1 for r in no_match_rows if r.no_match_correct) / len(no_match_rows)
                if no_match_rows
                else 1.0
            )
            adversarial_rows = [r for r in results if r.suite == "adversarial"]
            metrics.ambiguity_false_confidence_rate = (
                sum(1 for r in adversarial_rows if r.ambiguity_false_confidence) / len(adversarial_rows)
                if adversarial_rows
                else 0.0
            )

        # Grouped summary.
        grouped: dict[str, dict[str, Any]] = {}
        suites = sorted({r.suite for r in results})
        for suite in suites:
            rows = [r for r in results if r.suite == suite]
            grouped[suite] = {
                "count": len(rows),
                "pass_rate": (sum(1 for r in rows if r.passed) / len(rows)) if rows else 0.0,
                "strong_rate": (sum(1 for r in rows if r.evidence_quality == "STRONG") / len(rows)) if rows else 0.0,
                "weak_rate": (sum(1 for r in rows if r.evidence_quality == "WEAK") / len(rows)) if rows else 0.0,
                "insufficient_rate": (sum(1 for r in rows if r.evidence_quality == "INSUFFICIENT") / len(rows)) if rows else 0.0,
                "no_match_rate": (sum(1 for r in rows if r.evidence_quality == "NO_MATCH") / len(rows)) if rows else 0.0,
                "core_code_pct_top_k": (
                    sum(r.dominance_metrics.get("core_code_in_top_k_pct", 0.0) for r in rows) / len(rows)
                )
                if rows
                else 0.0,
            }
        metrics.grouped_summary = grouped
        
        return metrics

    def _evaluate_thresholds(self, metrics: ValidationMetrics) -> dict[str, bool]:
        code_intent_group = {
            "aiops_grounding",
            "debug",
            "plan_change",
        }
        core_vals = [
            g.get("core_code_pct_top_k", 0.0)
            for k, g in metrics.grouped_summary.items()
            if k in code_intent_group
        ]
        avg_core_code_pct = sum(core_vals) / len(core_vals) if core_vals else 0.0
        return {
            "min_core_code_pct_for_code_intent": (
                avg_core_code_pct >= self.thresholds.min_core_code_pct_for_code_intent
            ),
            "max_false_strong_rate": (
                metrics.false_strong_rate <= self.thresholds.max_false_strong_rate
            ),
            "min_weak_correctness_rate": (
                metrics.weak_correctness_rate >= self.thresholds.min_weak_correctness_rate
            ),
            "min_no_match_correctness_rate": (
                metrics.no_match_correctness_rate >= self.thresholds.min_no_match_correctness_rate
            ),
        }


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
