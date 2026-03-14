"""
Collapse Vector Classifier — M4.3 deterministic collapse detection.

Detects and classifies governance/runtime collapse vectors from runtime
evidence. Operates on existing evidence artifacts only; does not mutate
runtime state.

Collapse classes detected:
- identity_propagation_missing: canonical_hash absent in decision/execution rows
- decision_execution_mismatch: decision posture conflicts with execution outcome
- replay_mismatch: replayed execution differs from original
- missing_trace_linkage: trace lacks required join keys (request_id, plan_hash)
- unexpected_refusal_distribution_drift: refusal rate exceeds baseline threshold
- missing_evidence_join: plan/decision/execution cannot be linked
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.observation.collapse_models import (
    CollapseClass,
    CollapseEvent,
    CollapseEvidence,
    CollapseSeverity,
    create_collapse_event,
)


@dataclass
class ClassificationResult:
    """
    Result of collapse classification on a batch of evidence.
    
    Contains detected events and classification metadata.
    """
    
    events: list[CollapseEvent] = field(default_factory=list)
    items_processed: int = 0
    errors: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "events": [e.to_dict() for e in self.events],
            "items_processed": self.items_processed,
            "errors": self.errors,
            "events_count": len(self.events),
        }
    
    def has_collapses(self) -> bool:
        """Check if any collapse events were detected."""
        return len(self.events) > 0
    
    def has_critical(self) -> bool:
        """Check if any critical severity events exist."""
        return any(e.severity == CollapseSeverity.CRITICAL for e in self.events)


class CollapseClassifier:
    """
    Deterministic classifier for collapse vector detection.
    
    Analyzes runtime evidence (ledger rows, trace summaries, baseline
    comparisons) to detect collapse vectors. All detection is evidence-based
    and deterministic.
    """
    
    def __init__(
        self,
        refusal_drift_threshold: float = 0.02,
        require_canonical_hash: bool = True,
    ):
        """
        Initialize classifier with thresholds.
        
        Args:
            refusal_drift_threshold: Absolute threshold for refusal rate drift
            require_canonical_hash: Whether to flag missing canonical_hash as collapse
        """
        self.refusal_drift_threshold = refusal_drift_threshold
        self.require_canonical_hash = require_canonical_hash
    
    def classify_ledger_row(
        self,
        row: dict[str, Any],
        expected_posture: str | None = None,
    ) -> list[CollapseEvent]:
        """
        Classify a single ledger row for collapse vectors.
        
        Detects:
        - identity_propagation_missing (if canonical_hash required but absent)
        - missing_trace_linkage (if join keys missing)
        
        Args:
            row: Ledger row dictionary (ledger_row.v0.1 or payload dict)
            expected_posture: Expected decision posture for mismatch detection
        
        Returns:
            List of detected CollapseEvent instances
        """
        events: list[CollapseEvent] = []
        
        event_data = row.get("event", {})
        plan_link = row.get("plan_link", {})
        payload = row.get("payload", {})
        
        request_id = (
            event_data.get("request_id")
            or payload.get("request_id")
            or row.get("request_id", "")
        )
        plan_hash = (
            plan_link.get("plan_hash")
            or payload.get("plan_hash")
            or row.get("plan_hash", "")
        )
        canonical_hash = payload.get("canonical_hash") or row.get("canonical_hash")
        session_id = event_data.get("session_id", "")
        
        if self.require_canonical_hash and not canonical_hash:
            event_type = row.get("event_type") or event_data.get("event_type", "unknown")
            if event_type in (
                "plangate_safe_execute",
                "sandbox_executed",
                "execution_completed",
            ):
                evidence = CollapseEvidence(
                    evidence_type="ledger_row",
                    source_artifact=f"ledger:{request_id}",
                    field_path="payload.canonical_hash",
                    expected_value="<non-empty>",
                    actual_value=None,
                    context={"event_type": event_type},
                )
                events.append(
                    create_collapse_event(
                        collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
                        request_id=request_id,
                        plan_hash=plan_hash,
                        description=f"canonical_hash missing in {event_type} ledger row",
                        evidence=[evidence],
                        canonical_hash=canonical_hash,
                        session_id=session_id,
                    )
                )
        
        if not request_id and not plan_hash:
            evidence = CollapseEvidence(
                evidence_type="ledger_row",
                source_artifact="ledger:unknown",
                field_path="event.request_id,plan_link.plan_hash",
                expected_value="<at least one non-empty>",
                actual_value=None,
                context={"row_keys": list(row.keys())},
            )
            events.append(
                create_collapse_event(
                    collapse_class=CollapseClass.MISSING_TRACE_LINKAGE,
                    request_id=request_id,
                    plan_hash=plan_hash,
                    description="Ledger row lacks both request_id and plan_hash for linkage",
                    evidence=[evidence],
                    canonical_hash=canonical_hash,
                    session_id=session_id,
                )
            )
        
        return events
    
    def classify_decision_execution_pair(
        self,
        decision_row: dict[str, Any],
        execution_row: dict[str, Any],
    ) -> list[CollapseEvent]:
        """
        Classify a decision/execution pair for mismatches.
        
        Detects:
        - decision_execution_mismatch: decision posture vs execution outcome conflict
        - missing_evidence_join: rows cannot be linked
        
        Args:
            decision_row: Plan-Gate decision ledger row
            execution_row: Sandbox execution ledger row
        
        Returns:
            List of detected CollapseEvent instances
        """
        events: list[CollapseEvent] = []
        
        dec_event = decision_row.get("event", {})
        dec_payload = decision_row.get("payload", {})
        exec_event = execution_row.get("event", {})
        exec_payload = execution_row.get("payload", {})
        
        dec_request_id = dec_event.get("request_id") or dec_payload.get("request_id", "")
        exec_request_id = exec_event.get("request_id") or exec_payload.get("request_id", "")
        
        dec_plan_hash = (
            decision_row.get("plan_link", {}).get("plan_hash")
            or dec_payload.get("plan_hash", "")
        )
        exec_plan_hash = (
            execution_row.get("plan_link", {}).get("plan_hash")
            or exec_payload.get("plan_hash", "")
        )
        
        dec_canonical_hash = dec_payload.get("canonical_hash")
        exec_canonical_hash = exec_payload.get("canonical_hash")
        
        if dec_request_id and exec_request_id and dec_request_id != exec_request_id:
            evidence = CollapseEvidence(
                evidence_type="join_key_mismatch",
                source_artifact=f"decision:{dec_request_id},execution:{exec_request_id}",
                field_path="request_id",
                expected_value=dec_request_id,
                actual_value=exec_request_id,
                context={},
            )
            events.append(
                create_collapse_event(
                    collapse_class=CollapseClass.MISSING_EVIDENCE_JOIN,
                    request_id=dec_request_id,
                    plan_hash=dec_plan_hash,
                    description="Decision and execution rows have mismatched request_id",
                    evidence=[evidence],
                    canonical_hash=dec_canonical_hash,
                )
            )
            return events
        
        if dec_canonical_hash and exec_canonical_hash and dec_canonical_hash != exec_canonical_hash:
            evidence = CollapseEvidence(
                evidence_type="canonical_hash_mismatch",
                source_artifact=f"decision:{dec_request_id},execution:{exec_request_id}",
                field_path="canonical_hash",
                expected_value=dec_canonical_hash,
                actual_value=exec_canonical_hash,
                context={},
            )
            events.append(
                create_collapse_event(
                    collapse_class=CollapseClass.DECISION_EXECUTION_MISMATCH,
                    request_id=dec_request_id or exec_request_id,
                    plan_hash=dec_plan_hash or exec_plan_hash,
                    description="Decision and execution have different canonical_hash (artifact drift)",
                    evidence=[evidence],
                    canonical_hash=dec_canonical_hash,
                    severity=CollapseSeverity.CRITICAL,
                )
            )
        
        decision_posture = dec_payload.get("decision_posture") or decision_row.get(
            "verdicts", {}
        ).get("terminal_posture", "")
        
        exec_outcome = exec_payload.get("execution_outcome") or execution_row.get(
            "execution_outcome", ""
        )
        exec_exit_code = exec_payload.get("exit_code")
        
        if decision_posture == "safe_execute":
            if exec_outcome in ("refused", "blocked"):
                evidence = CollapseEvidence(
                    evidence_type="posture_outcome_conflict",
                    source_artifact=f"decision:{dec_request_id}",
                    field_path="decision_posture vs execution_outcome",
                    expected_value="execution allowed",
                    actual_value=exec_outcome,
                    context={
                        "decision_posture": decision_posture,
                        "execution_outcome": exec_outcome,
                    },
                )
                events.append(
                    create_collapse_event(
                        collapse_class=CollapseClass.DECISION_EXECUTION_MISMATCH,
                        request_id=dec_request_id or exec_request_id,
                        plan_hash=dec_plan_hash or exec_plan_hash,
                        description=f"Decision was safe_execute but execution was {exec_outcome}",
                        evidence=[evidence],
                        canonical_hash=dec_canonical_hash or exec_canonical_hash,
                    )
                )
        elif decision_posture in ("refuse", "defer", "bounded_allow"):
            if exec_outcome in ("success", "executed", "completed"):
                evidence = CollapseEvidence(
                    evidence_type="posture_outcome_conflict",
                    source_artifact=f"decision:{dec_request_id}",
                    field_path="decision_posture vs execution_outcome",
                    expected_value="execution blocked",
                    actual_value=exec_outcome,
                    context={
                        "decision_posture": decision_posture,
                        "execution_outcome": exec_outcome,
                    },
                )
                events.append(
                    create_collapse_event(
                        collapse_class=CollapseClass.DECISION_EXECUTION_MISMATCH,
                        request_id=dec_request_id or exec_request_id,
                        plan_hash=dec_plan_hash or exec_plan_hash,
                        description=f"Decision was {decision_posture} but execution succeeded",
                        evidence=[evidence],
                        canonical_hash=dec_canonical_hash or exec_canonical_hash,
                        severity=CollapseSeverity.CRITICAL,
                    )
                )
        
        return events
    
    def classify_replay_comparison(
        self,
        original: dict[str, Any],
        replayed: dict[str, Any],
    ) -> list[CollapseEvent]:
        """
        Classify a replay comparison for mismatches.
        
        Detects:
        - replay_mismatch: replayed execution differs from original
        
        Args:
            original: Original execution record
            replayed: Replayed execution record
        
        Returns:
            List of detected CollapseEvent instances
        """
        events: list[CollapseEvent] = []
        
        orig_request_id = original.get("request_id", "")
        orig_plan_hash = original.get("plan_hash", "")
        orig_canonical_hash = original.get("canonical_hash")
        replay_canonical_hash = replayed.get("canonical_hash")
        
        if orig_canonical_hash and replay_canonical_hash:
            if orig_canonical_hash != replay_canonical_hash:
                evidence = CollapseEvidence(
                    evidence_type="replay_hash_mismatch",
                    source_artifact=f"replay:{orig_request_id}",
                    field_path="canonical_hash",
                    expected_value=orig_canonical_hash,
                    actual_value=replay_canonical_hash,
                    context={},
                )
                events.append(
                    create_collapse_event(
                        collapse_class=CollapseClass.REPLAY_MISMATCH,
                        request_id=orig_request_id,
                        plan_hash=orig_plan_hash,
                        description="Replay canonical_hash differs from original",
                        evidence=[evidence],
                        canonical_hash=orig_canonical_hash,
                    )
                )
        
        orig_posture = original.get("terminal_posture") or original.get("decision_posture", "")
        replay_posture = replayed.get("terminal_posture") or replayed.get("decision_posture", "")
        
        if orig_posture and replay_posture and orig_posture != replay_posture:
            evidence = CollapseEvidence(
                evidence_type="replay_posture_mismatch",
                source_artifact=f"replay:{orig_request_id}",
                field_path="terminal_posture",
                expected_value=orig_posture,
                actual_value=replay_posture,
                context={},
            )
            events.append(
                create_collapse_event(
                    collapse_class=CollapseClass.REPLAY_MISMATCH,
                    request_id=orig_request_id,
                    plan_hash=orig_plan_hash,
                    description=f"Replay posture ({replay_posture}) differs from original ({orig_posture})",
                    evidence=[evidence],
                    canonical_hash=orig_canonical_hash,
                )
            )
        
        orig_exit = original.get("exit_code")
        replay_exit = replayed.get("exit_code")
        
        if orig_exit is not None and replay_exit is not None and orig_exit != replay_exit:
            evidence = CollapseEvidence(
                evidence_type="replay_exit_code_mismatch",
                source_artifact=f"replay:{orig_request_id}",
                field_path="exit_code",
                expected_value=str(orig_exit),
                actual_value=str(replay_exit),
                context={},
            )
            events.append(
                create_collapse_event(
                    collapse_class=CollapseClass.REPLAY_MISMATCH,
                    request_id=orig_request_id,
                    plan_hash=orig_plan_hash,
                    description=f"Replay exit_code ({replay_exit}) differs from original ({orig_exit})",
                    evidence=[evidence],
                    canonical_hash=orig_canonical_hash,
                    severity=CollapseSeverity.MEDIUM,
                )
            )
        
        return events
    
    def classify_baseline_drift(
        self,
        baseline_metrics: dict[str, Any],
        current_metrics: dict[str, Any],
    ) -> list[CollapseEvent]:
        """
        Classify baseline drift for unexpected refusal distribution changes.
        
        Detects:
        - unexpected_refusal_distribution_drift: refusal rate exceeds threshold
        
        Args:
            baseline_metrics: Baseline metrics from Day-0 snapshot
            current_metrics: Current metrics from recent batch
        
        Returns:
            List of detected CollapseEvent instances
        """
        events: list[CollapseEvent] = []
        
        base_refusal = baseline_metrics.get("refusal_rate", 0.0)
        curr_refusal = current_metrics.get("refusal_rate", 0.0)
        delta = abs(curr_refusal - base_refusal)
        
        if delta >= self.refusal_drift_threshold:
            evidence = CollapseEvidence(
                evidence_type="refusal_rate_drift",
                source_artifact="baseline_comparison",
                field_path="refusal_rate",
                expected_value=f"{base_refusal:.4f} ± {self.refusal_drift_threshold}",
                actual_value=f"{curr_refusal:.4f}",
                context={
                    "baseline_refusal_rate": base_refusal,
                    "current_refusal_rate": curr_refusal,
                    "delta": delta,
                    "threshold": self.refusal_drift_threshold,
                },
            )
            events.append(
                create_collapse_event(
                    collapse_class=CollapseClass.UNEXPECTED_REFUSAL_DISTRIBUTION_DRIFT,
                    request_id="",
                    plan_hash="",
                    description=f"Refusal rate drift {delta:.4f} exceeds threshold {self.refusal_drift_threshold}",
                    evidence=[evidence],
                )
            )
        
        base_crossed = baseline_metrics.get("crossed_count", 0)
        curr_crossed = current_metrics.get("crossed_count", 0)
        
        if curr_crossed > base_crossed:
            evidence = CollapseEvidence(
                evidence_type="boundary_crossed_increase",
                source_artifact="baseline_comparison",
                field_path="crossed_count",
                expected_value=f"<= {base_crossed}",
                actual_value=str(curr_crossed),
                context={
                    "baseline_crossed": base_crossed,
                    "current_crossed": curr_crossed,
                },
            )
            events.append(
                create_collapse_event(
                    collapse_class=CollapseClass.UNEXPECTED_REFUSAL_DISTRIBUTION_DRIFT,
                    request_id="",
                    plan_hash="",
                    description=f"Boundary crossed count increased from {base_crossed} to {curr_crossed}",
                    evidence=[evidence],
                    severity=CollapseSeverity.CRITICAL,
                )
            )
        
        return events
    
    def classify_trace_summary(
        self,
        trace: dict[str, Any],
    ) -> list[CollapseEvent]:
        """
        Classify a trace summary for linkage issues.
        
        Detects:
        - missing_trace_linkage: trace lacks required join keys
        - missing_evidence_join: incomplete plan/decision/execution chain
        
        Args:
            trace: Trace summary dictionary
        
        Returns:
            List of detected CollapseEvent instances
        """
        events: list[CollapseEvent] = []
        
        request_id = trace.get("request_id", "")
        plan_hash = trace.get("plan_hash", "")
        session_id = trace.get("session_id", "")
        
        if not request_id and not plan_hash:
            evidence = CollapseEvidence(
                evidence_type="trace_summary",
                source_artifact=f"trace:{session_id or 'unknown'}",
                field_path="request_id,plan_hash",
                expected_value="<at least one non-empty>",
                actual_value=None,
                context={"trace_keys": list(trace.keys())},
            )
            events.append(
                create_collapse_event(
                    collapse_class=CollapseClass.MISSING_TRACE_LINKAGE,
                    request_id=request_id,
                    plan_hash=plan_hash,
                    description="Trace summary lacks both request_id and plan_hash",
                    evidence=[evidence],
                    session_id=session_id,
                )
            )
        
        has_plan = trace.get("plan_event") is not None or trace.get("has_plan", False)
        has_decision = trace.get("decision_event") is not None or trace.get("has_decision", False)
        has_execution = trace.get("execution_event") is not None or trace.get("has_execution", False)
        final_posture = trace.get("final_posture") or trace.get("terminal_posture", "")
        
        if has_decision and final_posture == "safe_execute" and not has_execution:
            evidence = CollapseEvidence(
                evidence_type="incomplete_chain",
                source_artifact=f"trace:{request_id}",
                field_path="execution_event",
                expected_value="<present for safe_execute>",
                actual_value=None,
                context={
                    "has_plan": has_plan,
                    "has_decision": has_decision,
                    "final_posture": final_posture,
                },
            )
            events.append(
                create_collapse_event(
                    collapse_class=CollapseClass.MISSING_EVIDENCE_JOIN,
                    request_id=request_id,
                    plan_hash=plan_hash,
                    description="Decision was safe_execute but no execution event found",
                    evidence=[evidence],
                    session_id=session_id,
                )
            )
        
        if has_execution and not has_decision:
            evidence = CollapseEvidence(
                evidence_type="incomplete_chain",
                source_artifact=f"trace:{request_id}",
                field_path="decision_event",
                expected_value="<present before execution>",
                actual_value=None,
                context={
                    "has_plan": has_plan,
                    "has_execution": has_execution,
                },
            )
            events.append(
                create_collapse_event(
                    collapse_class=CollapseClass.MISSING_EVIDENCE_JOIN,
                    request_id=request_id,
                    plan_hash=plan_hash,
                    description="Execution event found but no decision event (bypass risk)",
                    evidence=[evidence],
                    session_id=session_id,
                    severity=CollapseSeverity.CRITICAL,
                )
            )
        
        return events
    
    def classify_batch(
        self,
        ledger_rows: list[dict[str, Any]] | None = None,
        trace_summaries: list[dict[str, Any]] | None = None,
        baseline_metrics: dict[str, Any] | None = None,
        current_metrics: dict[str, Any] | None = None,
    ) -> ClassificationResult:
        """
        Classify a batch of evidence for collapse vectors.
        
        Args:
            ledger_rows: List of ledger row dictionaries
            trace_summaries: List of trace summary dictionaries
            baseline_metrics: Baseline metrics for drift comparison
            current_metrics: Current metrics for drift comparison
        
        Returns:
            ClassificationResult with all detected events
        """
        result = ClassificationResult()
        
        if ledger_rows:
            for row in ledger_rows:
                try:
                    events = self.classify_ledger_row(row)
                    result.events.extend(events)
                    result.items_processed += 1
                except Exception as e:
                    result.errors.append(f"ledger_row error: {e}")
        
        if trace_summaries:
            for trace in trace_summaries:
                try:
                    events = self.classify_trace_summary(trace)
                    result.events.extend(events)
                    result.items_processed += 1
                except Exception as e:
                    result.errors.append(f"trace_summary error: {e}")
        
        if baseline_metrics and current_metrics:
            try:
                events = self.classify_baseline_drift(baseline_metrics, current_metrics)
                result.events.extend(events)
                result.items_processed += 1
            except Exception as e:
                result.errors.append(f"baseline_drift error: {e}")
        
        return result
