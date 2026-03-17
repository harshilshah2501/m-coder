"""
M4.1 Explanation Builder — Human-readable explanation payloads.

C2: Deterministic execution explanation from C1 trace (final outcome, decisive factors, evidence).
Uses only C1 trace event_type and metadata; no inference, no model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from runtime.observation.models import (
    ExecutionExplanation,
    ExplanationNotFoundError,
    ExplanationPayload,
)

if TYPE_CHECKING:
    from runtime.observation.trace_builder import TraceBuilder
    from runtime.observation.models import ExecutionTrace, TraceEvent


# Decision to human-readable outcome mapping
_DECISION_OUTCOMES = {
    "refused": "Request was refused by governance",
    "deferred": "Request was deferred for human review",
    "bounded_allow": "Request was conditionally allowed with restrictions",
    "safe_execute": "Request was approved for execution",
    "executed": "Command was executed successfully",
    "blocked": "Command execution was blocked by policy",
}

# Decision to explanation templates
_EXPLANATION_TEMPLATES = {
    "refused": "The runtime refused this request because: {reason}.",
    "deferred": "This request was deferred to human review because: {reason}.",
    "bounded_allow": "This request was conditionally allowed with restrictions: {reason}.",
    "safe_execute": "The runtime approved this request for execution.",
    "executed": "The command completed with exit code {exit_code}.",
    "blocked": "The command was blocked by sandbox policy: {reason}.",
}


# C2: event_type -> short factor phrase (deterministic, evidence-backed only)
_EVENT_TYPE_TO_FACTOR = {
    "REFUSED": "plan gate refused request",
    "PLAN_DEFERRED": "plan gate deferred execution",
    "PLAN_BOUNDED": "bounded allowance issued",
    "PLAN_APPROVED": "plan gate approved execution",
    "EXECUTION_BLOCKED": "execution was blocked in sandbox",
    "EXECUTION_COMPLETED": "sandbox completed execution",
    "UNKNOWN_EVENT": "unknown event in trace",
}


def _extract_decisive_factors(events: list["TraceEvent"], is_replay: bool) -> tuple[str, ...]:
    """Derive decisive factors from trace events only; dedupe, stable order."""
    seen: set[str] = set()
    out: list[str] = []
    for ev in events:
        factor = _EVENT_TYPE_TO_FACTOR.get(ev.event_type)
        if factor and factor not in seen:
            seen.add(factor)
            out.append(factor)
        # Optional: authority_verdict / boundary_verdict from payload (if present)
        payload = getattr(ev, "payload", None) or {}
        auth = payload.get("authority_verdict")
        if auth and auth != "pass" and (f := f"authority verdict was {auth}") not in seen:
            seen.add(f)
            out.append(f)
        bv = payload.get("boundary_verdict")
        if bv and (f := f"boundary verdict was {bv}") not in seen:
            seen.add(f)
            out.append(f)
    if is_replay and "request was replayed" not in seen:
        out.append("request was replayed")
    return tuple(out)


def _build_summary(final_outcome: str, factors: tuple[str, ...]) -> str:
    """Deterministic summary: <OUTCOME> because <factor1>, <factor2>."""
    if not factors:
        return f"{final_outcome} because no decisive factors extracted"
    return f"{final_outcome} because " + ", ".join(factors)


class ExplanationBuilder:
    """
    Build human-readable explanation payloads for plugin / UI consumption.
    C2: explain_trace / explain_from_request_id / explain_from_canonical_hash produce
    ExecutionExplanation from C1 trace only (deterministic, evidence-backed).
    """

    def __init__(self, trace_builder: "TraceBuilder | None" = None):
        """
        Args:
            trace_builder: Optional C1 TraceBuilder; required for explain_from_request_id / explain_from_canonical_hash.
        """
        self._trace_builder = trace_builder

    def explain_from_request_id(self, request_id: str) -> ExecutionExplanation:
        """Build execution explanation for a request_id using C1 trace (trace must exist)."""
        if not self._trace_builder:
            raise ValueError("TraceBuilder required for explain_from_request_id")
        trace = self._trace_builder.build_from_request_id(request_id)
        return self.explain_trace(trace)

    def explain_from_canonical_hash(self, canonical_hash: str) -> ExecutionExplanation:
        """Build execution explanation by canonical_hash using C1 trace (latest request group only)."""
        if not self._trace_builder:
            raise ValueError("TraceBuilder required for explain_from_canonical_hash")
        trace = self._trace_builder.build_from_canonical_hash(canonical_hash)
        return self.explain_trace(trace)

    def explain_trace(self, trace: "ExecutionTrace") -> ExecutionExplanation:
        """
        Build deterministic ExecutionExplanation from a C1 ExecutionTrace.
        Raises ExplanationNotFoundError if trace has no events.
        """
        events = trace.events or []
        if not events:
            raise ExplanationNotFoundError(
                f"No events in trace (trace_id={trace.trace_id!r}, lookup_type={trace.lookup_type!r})"
            )
        last = events[-1]
        final_outcome = last.event_type
        factors = _extract_decisive_factors(events, trace.is_replay)
        summary = _build_summary(final_outcome, factors)
        evidence_refs = tuple(f"event[{i}]" for i in range(len(events)))
        return ExecutionExplanation(
            request_id=trace.request_id or None,
            canonical_hash=trace.canonical_hash or None,
            final_outcome=final_outcome,
            summary=summary,
            decisive_factors=factors,
            evidence_refs=evidence_refs,
            is_replay=trace.is_replay,
        )

    def build_from_trace_event(self, event: Any) -> ExplanationPayload:
        """
        Build explanation from a TraceEvent.
        
        Args:
            event: TraceEvent or dict with event data
            
        Returns:
            ExplanationPayload with human-readable explanation
        """
        if hasattr(event, "to_dict"):
            data = event.to_dict()
        else:
            data = event
        
        decision = data.get("posture", "")
        reason = data.get("reason", "")
        
        outcome = _DECISION_OUTCOMES.get(decision, f"Decision: {decision}")
        
        # Build explanation
        template = _EXPLANATION_TEMPLATES.get(decision, "Request processed: {reason}")
        exit_code = data.get("exit_code")
        explanation = template.format(
            reason=reason or "no details available",
            exit_code=exit_code if exit_code is not None else "N/A",
        )
        
        return ExplanationPayload(
            decision=decision,
            outcome=outcome,
            reason=reason,
            canonical_hash=data.get("canonical_hash", ""),
            request_id=data.get("request_id", ""),
            backend=data.get("backend", ""),
            execution_surface=data.get("execution_surface", ""),
            explanation=explanation,
            exit_code=exit_code,
            duration_ms=data.get("duration_ms"),
            artifacts=data.get("artifacts", []),
        )
    
    def build_from_ledger_row(self, row: Any) -> ExplanationPayload:
        """
        Build explanation from a SandboxLedgerStore LedgerRow.
        
        Args:
            row: LedgerRow from sandbox ledger store
            
        Returns:
            ExplanationPayload with human-readable explanation
        """
        payload = row.payload if hasattr(row, "payload") else {}
        
        # Map event_type to decision
        event_type = row.event_type if hasattr(row, "event_type") else ""
        decision = self._event_type_to_decision(event_type)
        
        reason = (
            payload.get("reason", "") or 
            payload.get("refusal_reason", "") or 
            payload.get("blocked_reason", "") or
            payload.get("decision_posture", "")
        )
        
        outcome = _DECISION_OUTCOMES.get(decision, f"Event: {event_type}")
        
        # Build explanation
        exit_code = payload.get("exit_code")
        template = _EXPLANATION_TEMPLATES.get(decision, "Request processed: {reason}")
        explanation = template.format(
            reason=reason or "no details available",
            exit_code=exit_code if exit_code is not None else "N/A",
        )
        
        return ExplanationPayload(
            decision=decision,
            outcome=outcome,
            reason=reason,
            canonical_hash=payload.get("canonical_hash", ""),
            request_id=row.request_id if hasattr(row, "request_id") else "",
            backend=payload.get("backend", ""),
            execution_surface=payload.get("execution_surface", ""),
            explanation=explanation,
            exit_code=exit_code,
            duration_ms=payload.get("duration_ms"),
            artifacts=payload.get("artifacts", []),
        )
    
    def build_from_governed_result(self, result: Any) -> ExplanationPayload:
        """
        Build explanation from a GovernedExecutionResult.
        
        Args:
            result: GovernedExecutionResult from sandbox executor
            
        Returns:
            ExplanationPayload with human-readable explanation
        """
        if hasattr(result, "to_dict"):
            data = result.to_dict()
        else:
            data = result
        
        outcome_type = data.get("outcome_type", "")
        decision = self._outcome_type_to_decision(outcome_type)
        
        reason = (
            data.get("refusal_reason", "") or 
            data.get("blocked_reason", "") or
            ""
        )
        
        outcome = _DECISION_OUTCOMES.get(decision, f"Outcome: {outcome_type}")
        
        # Build explanation
        exit_code = data.get("exit_code")
        template = _EXPLANATION_TEMPLATES.get(decision, "Request processed: {reason}")
        explanation = template.format(
            reason=reason or "no details available",
            exit_code=exit_code if exit_code is not None else "N/A",
        )
        
        return ExplanationPayload(
            decision=decision,
            outcome=outcome,
            reason=reason,
            canonical_hash=data.get("canonical_hash", ""),
            request_id=data.get("request_id", ""),
            backend=data.get("backend", ""),
            execution_surface=data.get("execution_surface", ""),
            explanation=explanation,
            exit_code=exit_code,
            duration_ms=data.get("duration_ms"),
            artifacts=data.get("artifacts", []),
        )
    
    def build_summary_explanation(
        self,
        decision: str,
        reason: str,
        canonical_hash: str = "",
        request_id: str = "",
        backend: str = "",
        execution_surface: str = "",
        exit_code: int | None = None,
        duration_ms: int | None = None,
    ) -> ExplanationPayload:
        """
        Build explanation from individual fields.
        
        Args:
            decision: The decision posture
            reason: The reason for the decision
            canonical_hash: Optional canonical execution hash
            request_id: Optional request identifier
            backend: Optional backend used
            execution_surface: Optional execution surface
            exit_code: Optional exit code
            duration_ms: Optional duration in milliseconds
            
        Returns:
            ExplanationPayload with human-readable explanation
        """
        outcome = _DECISION_OUTCOMES.get(decision, f"Decision: {decision}")
        
        template = _EXPLANATION_TEMPLATES.get(decision, "Request processed: {reason}")
        explanation = template.format(
            reason=reason or "no details available",
            exit_code=exit_code if exit_code is not None else "N/A",
        )
        
        return ExplanationPayload(
            decision=decision,
            outcome=outcome,
            reason=reason,
            canonical_hash=canonical_hash,
            request_id=request_id,
            backend=backend,
            execution_surface=execution_surface,
            explanation=explanation,
            exit_code=exit_code,
            duration_ms=duration_ms,
        )
    
    @staticmethod
    def _event_type_to_decision(event_type: str) -> str:
        """Map ledger event type to decision."""
        mapping = {
            "plangate_refused": "refused",
            "plangate_deferred": "deferred",
            "plangate_bounded_allow": "bounded_allow",
            "plangate_safe_execute": "safe_execute",
            "sandbox_refused": "refused",
            "sandbox_blocked": "blocked",
            "sandbox_executed": "executed",
        }
        return mapping.get(event_type, event_type)
    
    @staticmethod
    def _outcome_type_to_decision(outcome_type: str) -> str:
        """Map GovernedExecutionResult outcome_type to decision."""
        mapping = {
            "refused": "refused",
            "blocked": "blocked",
            "executed": "executed",
        }
        return mapping.get(outcome_type, outcome_type)
