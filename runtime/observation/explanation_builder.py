"""
M4.1 Explanation Builder — Human-readable explanation payloads.

Requirements:
- decision / outcome
- reason
- canonical_hash
- backend
- execution_surface
- concise human-readable explanation
"""

from __future__ import annotations

from typing import Any

from runtime.observation.models import ExplanationPayload


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


class ExplanationBuilder:
    """
    Build human-readable explanation payloads for plugin / UI consumption.
    
    Transforms raw ledger data into concise, actionable explanations.
    """
    
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
