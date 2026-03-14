"""
Ledger Reconciliation Service — M4.4.

Reconciles plan, decision, execution, and replay evidence using
request_id, plan_hash, and canonical_hash linkage.

Key responsibilities:
- Verify request_id linkage across rows
- Verify plan_hash linkage between decision and plan
- Verify canonical_hash linkage between decision and execution
- Detect missing decision/execution rows
- Detect replay linkage where replay occurred
- Classify mismatches deterministically

Constraints:
- Read-only over evidence
- No mutation of existing ledger rows
- Backward compatible with older rows missing identity fields
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from runtime.observation.reconciliation_models import (
    MismatchClassification,
    MismatchSeverity,
    ReconciliationMismatch,
    ReconciliationResult,
    ReconciliationStatus,
    RowLinkage,
)
from runtime.sandbox.sandbox_ledger_store import (
    EVENT_EXECUTED,
    EVENT_PLANGATE_BOUNDED_ALLOW,
    EVENT_PLANGATE_DEFERRED,
    EVENT_PLANGATE_REFUSED,
    EVENT_PLANGATE_SAFE_EXECUTE,
)

if TYPE_CHECKING:
    from runtime.sandbox.sandbox_ledger_store import LedgerRow, SandboxLedgerStore


DECISION_EVENT_TYPES = frozenset({
    EVENT_PLANGATE_REFUSED,
    EVENT_PLANGATE_DEFERRED,
    EVENT_PLANGATE_BOUNDED_ALLOW,
    EVENT_PLANGATE_SAFE_EXECUTE,
})

EXECUTION_EVENT_TYPES = frozenset({
    EVENT_EXECUTED,
    "sandbox_blocked",
    "sandbox_refused",
})


@dataclass
class ReconciliationConfig:
    """Configuration for reconciliation behavior.
    
    Controls which checks are performed and severity mapping.
    """
    
    check_canonical_hash: bool = True
    check_plan_hash: bool = True
    check_intent_id: bool = True
    check_replay_linkage: bool = True
    check_invariants: bool = True
    treat_legacy_as_warning: bool = True
    require_execution_for_safe_execute: bool = True


class LedgerReconciliationService:
    """
    Service for reconciling ledger evidence.
    
    Performs read-only verification of linkage consistency between
    plan-gate decisions and sandbox executions using identity fields.
    
    Usage:
        store = SandboxLedgerStore(path)
        service = LedgerReconciliationService(store)
        
        # Reconcile by request_id
        result = service.reconcile_by_request_id("req-123")
        
        # Reconcile by canonical_hash
        result = service.reconcile_by_canonical_hash("abc123...")
        
        # Reconcile all rows
        result = service.reconcile_all()
    """
    
    def __init__(
        self,
        ledger_store: SandboxLedgerStore,
        config: ReconciliationConfig | None = None,
    ) -> None:
        """
        Initialize reconciliation service.
        
        Args:
            ledger_store: SandboxLedgerStore to read from
            config: Optional configuration (defaults provided)
        """
        self.ledger_store = ledger_store
        self.config = config or ReconciliationConfig()
    
    def reconcile_by_request_id(self, request_id: str) -> ReconciliationResult:
        """
        Reconcile all ledger rows for a given request_id.
        
        Verifies:
        - Decision row exists where expected
        - Execution row exists where expected (for safe_execute)
        - Canonical_hash matches between decision and execution
        - Plan_hash consistency
        - No duplicate decisions/executions for same canonical_hash
        
        Args:
            request_id: Request identifier to reconcile
            
        Returns:
            ReconciliationResult with linkages and mismatches
        """
        rows = self.ledger_store.get_by_request_id(request_id)
        
        result = ReconciliationResult(
            status=ReconciliationStatus.CONSISTENT,
            scope_request_id=request_id,
            total_rows_examined=len(rows),
        )
        
        if not rows:
            return result
        
        linkages, decision_rows, execution_rows = self._extract_row_groups(rows)
        result.linkages = linkages
        result.decision_rows_found = len(decision_rows)
        result.execution_rows_found = len(execution_rows)
        result.legacy_rows_found = sum(1 for l in linkages if not l.has_canonical_hash)
        
        self._check_decision_execution_linkage(
            request_id, decision_rows, execution_rows, linkages, result
        )
        self._check_canonical_hash_consistency(request_id, linkages, result)
        self._check_plan_hash_consistency(request_id, linkages, result)
        self._check_duplicates(request_id, linkages, result)
        self._check_legacy_rows(request_id, linkages, result)
        
        result.status = self._compute_status(result.mismatches)
        return result
    
    def reconcile_by_canonical_hash(self, canonical_hash: str) -> ReconciliationResult:
        """
        Reconcile all ledger rows for a given canonical_hash.
        
        Verifies that decision and execution rows with this canonical_hash
        are consistent and properly linked.
        
        Args:
            canonical_hash: Canonical hash to reconcile
            
        Returns:
            ReconciliationResult with linkages and mismatches
        """
        rows = self.ledger_store.get_by_canonical_hash(canonical_hash)
        
        result = ReconciliationResult(
            status=ReconciliationStatus.CONSISTENT,
            scope_canonical_hash=canonical_hash,
            total_rows_examined=len(rows),
        )
        
        if not rows:
            return result
        
        linkages, decision_rows, execution_rows = self._extract_row_groups(rows)
        result.linkages = linkages
        result.decision_rows_found = len(decision_rows)
        result.execution_rows_found = len(execution_rows)
        
        request_ids = {l.request_id for l in linkages}
        for req_id in request_ids:
            req_linkages = [l for l in linkages if l.request_id == req_id]
            req_decisions = [r for r in decision_rows if r.request_id == req_id]
            req_executions = [r for r in execution_rows if r.request_id == req_id]
            
            self._check_decision_execution_linkage(
                req_id, req_decisions, req_executions, req_linkages, result
            )
        
        self._check_intent_id_consistency(canonical_hash, linkages, result)
        self._check_duplicates_by_canonical_hash(canonical_hash, linkages, result)
        
        result.status = self._compute_status(result.mismatches)
        return result
    
    def reconcile_by_plan_hash(self, plan_hash: str) -> ReconciliationResult:
        """
        Reconcile all ledger rows for a given plan_hash.
        
        Args:
            plan_hash: Plan hash to reconcile
            
        Returns:
            ReconciliationResult with linkages and mismatches
        """
        all_rows = self.ledger_store.list_all()
        rows = [
            r for r in all_rows
            if r.plan_hash == plan_hash or r.payload.get("plan_hash") == plan_hash
        ]
        
        result = ReconciliationResult(
            status=ReconciliationStatus.CONSISTENT,
            scope_plan_hash=plan_hash,
            total_rows_examined=len(rows),
        )
        
        if not rows:
            return result
        
        linkages, decision_rows, execution_rows = self._extract_row_groups(rows)
        result.linkages = linkages
        result.decision_rows_found = len(decision_rows)
        result.execution_rows_found = len(execution_rows)
        result.legacy_rows_found = sum(1 for l in linkages if not l.has_canonical_hash)
        
        request_ids = {l.request_id for l in linkages}
        for req_id in request_ids:
            req_linkages = [l for l in linkages if l.request_id == req_id]
            req_decisions = [r for r in decision_rows if r.request_id == req_id]
            req_executions = [r for r in execution_rows if r.request_id == req_id]
            
            self._check_decision_execution_linkage(
                req_id, req_decisions, req_executions, req_linkages, result
            )
        
        result.status = self._compute_status(result.mismatches)
        return result
    
    def reconcile_all(self) -> ReconciliationResult:
        """
        Reconcile all ledger rows.
        
        Performs comprehensive consistency check across entire ledger.
        Use with caution on large ledgers.
        
        Returns:
            ReconciliationResult with all linkages and mismatches
        """
        all_rows = self.ledger_store.list_all()
        
        result = ReconciliationResult(
            status=ReconciliationStatus.CONSISTENT,
            total_rows_examined=len(all_rows),
        )
        
        if not all_rows:
            return result
        
        linkages, decision_rows, execution_rows = self._extract_row_groups(all_rows)
        result.linkages = linkages
        result.decision_rows_found = len(decision_rows)
        result.execution_rows_found = len(execution_rows)
        result.legacy_rows_found = sum(1 for l in linkages if not l.has_canonical_hash)
        
        request_ids = {l.request_id for l in linkages if l.request_id}
        for req_id in request_ids:
            req_linkages = [l for l in linkages if l.request_id == req_id]
            req_decisions = [r for r in decision_rows if r.request_id == req_id]
            req_executions = [r for r in execution_rows if r.request_id == req_id]
            
            self._check_decision_execution_linkage(
                req_id, req_decisions, req_executions, req_linkages, result
            )
            self._check_canonical_hash_consistency(req_id, req_linkages, result)
            self._check_plan_hash_consistency(req_id, req_linkages, result)
        
        self._check_orphan_rows(linkages, result)
        self._check_legacy_rows("", linkages, result)
        
        result.status = self._compute_status(result.mismatches)
        return result
    
    def reconcile_replay_linkage(
        self,
        original_canonical_hash: str,
        replay_request_id: str,
    ) -> ReconciliationResult:
        """
        Verify replay linkage between original execution and replay.
        
        Checks that replay execution is properly linked to original
        via canonical_hash and execution_surface metadata.
        
        Args:
            original_canonical_hash: Canonical hash of original execution
            replay_request_id: Request ID of replay execution
            
        Returns:
            ReconciliationResult with replay linkage verification
        """
        result = ReconciliationResult(
            status=ReconciliationStatus.CONSISTENT,
            scope_canonical_hash=original_canonical_hash,
            scope_request_id=replay_request_id,
        )
        
        original_rows = self.ledger_store.get_by_canonical_hash(original_canonical_hash)
        replay_rows = self.ledger_store.get_by_request_id(replay_request_id)
        
        result.total_rows_examined = len(original_rows) + len(replay_rows)
        
        original_linkages, _, original_exec = self._extract_row_groups(original_rows)
        replay_linkages, _, replay_exec = self._extract_row_groups(replay_rows)
        
        result.linkages = original_linkages + replay_linkages
        result.execution_rows_found = len(original_exec) + len(replay_exec)
        result.replay_rows_found = len(replay_exec)
        
        if not original_exec:
            result.mismatches.append(ReconciliationMismatch(
                classification=MismatchClassification.MISSING_EXECUTION,
                severity=MismatchSeverity.ERROR,
                description=f"No original execution found for canonical_hash {original_canonical_hash}",
                request_id="",
                expected_value=original_canonical_hash,
            ))
        
        if replay_exec:
            for row in replay_exec:
                payload = row.payload or {}
                exec_surface = payload.get("execution_surface", "")
                replay_ch = payload.get("canonical_hash", "")
                
                if exec_surface != "replay":
                    result.mismatches.append(ReconciliationMismatch(
                        classification=MismatchClassification.MISSING_REPLAY_LINK,
                        severity=MismatchSeverity.WARNING,
                        description=f"Replay execution missing execution_surface=replay",
                        request_id=replay_request_id,
                        affected_rows=[row.ledger_row_id],
                        expected_value="replay",
                        actual_value=exec_surface,
                    ))
                
                if replay_ch and replay_ch != original_canonical_hash:
                    result.mismatches.append(ReconciliationMismatch(
                        classification=MismatchClassification.CANONICAL_HASH_MISMATCH,
                        severity=MismatchSeverity.WARNING,
                        description=f"Replay canonical_hash differs from original",
                        request_id=replay_request_id,
                        affected_rows=[row.ledger_row_id],
                        expected_value=original_canonical_hash,
                        actual_value=replay_ch,
                    ))
        
        result.status = self._compute_status(result.mismatches)
        return result
    
    def _extract_row_groups(
        self,
        rows: list[LedgerRow],
    ) -> tuple[list[RowLinkage], list[LedgerRow], list[LedgerRow]]:
        """Extract linkages and group rows by type."""
        linkages = []
        decision_rows = []
        execution_rows = []
        
        for row in rows:
            linkage = RowLinkage.from_sandbox_row(row)
            linkages.append(linkage)
            
            if row.event_type in DECISION_EVENT_TYPES:
                decision_rows.append(row)
            elif row.event_type in EXECUTION_EVENT_TYPES:
                execution_rows.append(row)
        
        return linkages, decision_rows, execution_rows
    
    def _check_decision_execution_linkage(
        self,
        request_id: str,
        decision_rows: list[LedgerRow],
        execution_rows: list[LedgerRow],
        linkages: list[RowLinkage],
        result: ReconciliationResult,
    ) -> None:
        """Check that decisions and executions are properly linked."""
        if not self.config.require_execution_for_safe_execute:
            return
        
        safe_execute_decisions = [
            r for r in decision_rows
            if r.event_type == EVENT_PLANGATE_SAFE_EXECUTE
        ]
        
        for decision in safe_execute_decisions:
            decision_payload = decision.payload or {}
            decision_ch = decision_payload.get("canonical_hash", "")
            
            matching_executions = [
                e for e in execution_rows
                if e.payload.get("canonical_hash") == decision_ch and decision_ch
            ]
            
            if not matching_executions and decision_ch:
                result.mismatches.append(ReconciliationMismatch(
                    classification=MismatchClassification.MISSING_EXECUTION,
                    severity=MismatchSeverity.ERROR,
                    description=f"safe_execute decision has no matching execution row",
                    request_id=request_id,
                    affected_rows=[decision.ledger_row_id],
                    expected_value=decision_ch,
                    context={"decision_event": decision.event_type},
                ))
        
        for execution in execution_rows:
            exec_payload = execution.payload or {}
            exec_ch = exec_payload.get("canonical_hash", "")
            
            if exec_ch:
                matching_decisions = [
                    d for d in decision_rows
                    if d.payload.get("canonical_hash") == exec_ch
                ]
                
                if not matching_decisions:
                    result.mismatches.append(ReconciliationMismatch(
                        classification=MismatchClassification.MISSING_DECISION,
                        severity=MismatchSeverity.ERROR,
                        description=f"Execution row has no matching decision row",
                        request_id=request_id,
                        affected_rows=[execution.ledger_row_id],
                        expected_value=exec_ch,
                        context={"execution_event": execution.event_type},
                    ))
    
    def _check_canonical_hash_consistency(
        self,
        request_id: str,
        linkages: list[RowLinkage],
        result: ReconciliationResult,
    ) -> None:
        """Check canonical_hash consistency within request."""
        if not self.config.check_canonical_hash:
            return
        
        canonical_hashes = {
            l.canonical_hash for l in linkages
            if l.has_canonical_hash and l.request_id == request_id
        }
        
        if len(canonical_hashes) > 1:
            result.mismatches.append(ReconciliationMismatch(
                classification=MismatchClassification.CANONICAL_HASH_MISMATCH,
                severity=MismatchSeverity.ERROR,
                description=f"Multiple canonical_hash values found for request {request_id}",
                request_id=request_id,
                affected_rows=[l.ledger_row_id for l in linkages if l.request_id == request_id],
                context={"canonical_hashes": list(canonical_hashes)},
            ))
    
    def _check_plan_hash_consistency(
        self,
        request_id: str,
        linkages: list[RowLinkage],
        result: ReconciliationResult,
    ) -> None:
        """Check plan_hash consistency within request."""
        if not self.config.check_plan_hash:
            return
        
        plan_hashes = {
            l.plan_hash for l in linkages
            if l.plan_hash and l.request_id == request_id
        }
        
        if len(plan_hashes) > 1:
            result.mismatches.append(ReconciliationMismatch(
                classification=MismatchClassification.PLAN_HASH_MISMATCH,
                severity=MismatchSeverity.WARNING,
                description=f"Multiple plan_hash values found for request {request_id}",
                request_id=request_id,
                affected_rows=[l.ledger_row_id for l in linkages if l.request_id == request_id],
                context={"plan_hashes": list(plan_hashes)},
            ))
    
    def _check_intent_id_consistency(
        self,
        canonical_hash: str,
        linkages: list[RowLinkage],
        result: ReconciliationResult,
    ) -> None:
        """Check intent_id consistency for same canonical_hash."""
        if not self.config.check_intent_id:
            return
        
        intent_ids = {
            l.intent_id for l in linkages
            if l.has_intent_id and l.canonical_hash == canonical_hash
        }
        
        if len(intent_ids) > 1:
            result.mismatches.append(ReconciliationMismatch(
                classification=MismatchClassification.INTENT_ID_MISMATCH,
                severity=MismatchSeverity.WARNING,
                description=f"Multiple intent_id values for canonical_hash {canonical_hash}",
                request_id="",
                affected_rows=[l.ledger_row_id for l in linkages if l.canonical_hash == canonical_hash],
                context={"intent_ids": list(intent_ids)},
            ))
    
    def _check_duplicates(
        self,
        request_id: str,
        linkages: list[RowLinkage],
        result: ReconciliationResult,
    ) -> None:
        """Check for duplicate decision or execution rows."""
        decision_hashes: dict[str, list[str]] = {}
        execution_hashes: dict[str, list[str]] = {}
        
        for l in linkages:
            if not l.has_canonical_hash or l.request_id != request_id:
                continue
            
            if l.event_type in DECISION_EVENT_TYPES:
                if l.canonical_hash not in decision_hashes:
                    decision_hashes[l.canonical_hash] = []
                decision_hashes[l.canonical_hash].append(l.ledger_row_id)
            
            if l.event_type in EXECUTION_EVENT_TYPES:
                if l.canonical_hash not in execution_hashes:
                    execution_hashes[l.canonical_hash] = []
                execution_hashes[l.canonical_hash].append(l.ledger_row_id)
        
        for ch, row_ids in decision_hashes.items():
            if len(row_ids) > 1:
                result.mismatches.append(ReconciliationMismatch(
                    classification=MismatchClassification.DUPLICATE_DECISION,
                    severity=MismatchSeverity.WARNING,
                    description=f"Multiple decision rows for canonical_hash {ch}",
                    request_id=request_id,
                    affected_rows=row_ids,
                ))
        
        for ch, row_ids in execution_hashes.items():
            if len(row_ids) > 1:
                result.mismatches.append(ReconciliationMismatch(
                    classification=MismatchClassification.DUPLICATE_EXECUTION,
                    severity=MismatchSeverity.WARNING,
                    description=f"Multiple execution rows for canonical_hash {ch}",
                    request_id=request_id,
                    affected_rows=row_ids,
                ))
    
    def _check_duplicates_by_canonical_hash(
        self,
        canonical_hash: str,
        linkages: list[RowLinkage],
        result: ReconciliationResult,
    ) -> None:
        """Check for duplicates scoped to a canonical_hash."""
        decisions = [
            l for l in linkages
            if l.canonical_hash == canonical_hash and l.event_type in DECISION_EVENT_TYPES
        ]
        executions = [
            l for l in linkages
            if l.canonical_hash == canonical_hash and l.event_type in EXECUTION_EVENT_TYPES
        ]
        
        if len(decisions) > 1:
            result.mismatches.append(ReconciliationMismatch(
                classification=MismatchClassification.DUPLICATE_DECISION,
                severity=MismatchSeverity.WARNING,
                description=f"Multiple decision rows for canonical_hash {canonical_hash}",
                request_id="",
                affected_rows=[d.ledger_row_id for d in decisions],
            ))
        
        if len(executions) > 1:
            result.mismatches.append(ReconciliationMismatch(
                classification=MismatchClassification.DUPLICATE_EXECUTION,
                severity=MismatchSeverity.WARNING,
                description=f"Multiple execution rows for canonical_hash {canonical_hash}",
                request_id="",
                affected_rows=[e.ledger_row_id for e in executions],
            ))
    
    def _check_orphan_rows(
        self,
        linkages: list[RowLinkage],
        result: ReconciliationResult,
    ) -> None:
        """Check for orphan rows (single row with unique request_id)."""
        request_counts: dict[str, int] = {}
        for l in linkages:
            if l.request_id:
                request_counts[l.request_id] = request_counts.get(l.request_id, 0) + 1
        
        for l in linkages:
            if l.request_id and request_counts[l.request_id] == 1:
                if l.event_type in EXECUTION_EVENT_TYPES and not l.has_canonical_hash:
                    continue
                
                if l.event_type in DECISION_EVENT_TYPES:
                    payload_ch = l.canonical_hash
                    if not payload_ch:
                        continue
    
    def _check_legacy_rows(
        self,
        request_id: str,
        linkages: list[RowLinkage],
        result: ReconciliationResult,
    ) -> None:
        """Check for legacy rows without identity fields."""
        if not self.config.treat_legacy_as_warning:
            return
        
        for l in linkages:
            if request_id and l.request_id != request_id:
                continue
            
            if not l.has_canonical_hash and l.event_type in (
                DECISION_EVENT_TYPES | EXECUTION_EVENT_TYPES
            ):
                result.mismatches.append(ReconciliationMismatch(
                    classification=MismatchClassification.LEGACY_ROW_NO_IDENTITY,
                    severity=MismatchSeverity.INFO,
                    description=f"Row missing canonical_hash (legacy format)",
                    request_id=l.request_id,
                    affected_rows=[l.ledger_row_id],
                    context={"event_type": l.event_type},
                ))
    
    def _compute_status(
        self,
        mismatches: list[ReconciliationMismatch],
    ) -> ReconciliationStatus:
        """Compute overall status from mismatches."""
        if not mismatches:
            return ReconciliationStatus.CONSISTENT
        
        severities = {m.severity for m in mismatches}
        
        if MismatchSeverity.CRITICAL in severities:
            return ReconciliationStatus.CRITICAL_MISMATCHES
        
        if MismatchSeverity.ERROR in severities:
            return ReconciliationStatus.MISMATCHES_FOUND
        
        if MismatchSeverity.WARNING in severities:
            return ReconciliationStatus.WARNINGS_ONLY
        
        return ReconciliationStatus.WARNINGS_ONLY
