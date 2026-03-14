"""
M4.4 Ledger Reconciliation Tests.

Verifies:
1. request_id linkage between decision and execution
2. plan_hash linkage consistency
3. canonical_hash linkage between decision and execution
4. Missing decision/execution detection
5. Replay linkage verification
6. Mismatch classification determinism
7. Backward compatibility with legacy rows
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.observation.reconciliation import (
    LedgerReconciliationService,
    ReconciliationConfig,
)
from runtime.observation.reconciliation_models import (
    MismatchClassification,
    MismatchSeverity,
    ReconciliationResult,
    ReconciliationStatus,
    RowLinkage,
)
from runtime.sandbox.sandbox_ledger_store import (
    EVENT_EXECUTED,
    EVENT_PLANGATE_SAFE_EXECUTE,
    EVENT_PLANGATE_REFUSED,
    SandboxLedgerStore,
)


class TestRowLinkage:
    """Test RowLinkage extraction from ledger rows."""
    
    def test_linkage_from_sandbox_row_with_identity(self) -> None:
        """RowLinkage extracts canonical_hash and intent_id from payload."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            store.append(
                ledger_row_id="row-1",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-1",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-abc123",
                    "intent_id": "intent-1",
                    "request_id": "req-1",
                    "plan_hash": "ph-1",
                },
            )
            
            rows = store.get_by_request_id("req-1")
            assert len(rows) == 1
            
            linkage = RowLinkage.from_sandbox_row(rows[0])
            
            assert linkage.ledger_row_id == "row-1"
            assert linkage.request_id == "req-1"
            assert linkage.canonical_hash == "ch-abc123"
            assert linkage.intent_id == "intent-1"
            assert linkage.plan_hash == "ph-1"
            assert linkage.has_canonical_hash is True
            assert linkage.has_intent_id is True
    
    def test_linkage_from_legacy_row_no_identity(self) -> None:
        """RowLinkage handles legacy rows without canonical_hash."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            store.append(
                ledger_row_id="legacy-1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-legacy",
                plan_hash="ph-legacy",
                sandbox_id="",
                payload={
                    "outcome_type": "executed",
                    "success": True,
                },
            )
            
            rows = store.get_by_request_id("req-legacy")
            linkage = RowLinkage.from_sandbox_row(rows[0])
            
            assert linkage.ledger_row_id == "legacy-1"
            assert linkage.request_id == "req-legacy"
            assert linkage.canonical_hash == ""
            assert linkage.has_canonical_hash is False
            assert linkage.has_intent_id is False
    
    def test_linkage_to_dict(self) -> None:
        """RowLinkage.to_dict() produces serializable output."""
        linkage = RowLinkage(
            ledger_row_id="row-1",
            event_type="plangate_safe_execute",
            request_id="req-1",
            plan_hash="ph-1",
            canonical_hash="ch-1",
            intent_id="intent-1",
            timestamp_utc="2026-03-13T12:00:00Z",
            has_canonical_hash=True,
            has_intent_id=True,
        )
        
        d = linkage.to_dict()
        
        assert d["ledger_row_id"] == "row-1"
        assert d["canonical_hash"] == "ch-1"
        assert d["has_canonical_hash"] is True


class TestReconciliationResult:
    """Test ReconciliationResult model."""
    
    def test_consistent_result(self) -> None:
        """Consistent result has no mismatches."""
        result = ReconciliationResult(
            status=ReconciliationStatus.CONSISTENT,
            scope_request_id="req-1",
            total_rows_examined=2,
        )
        
        assert result.is_consistent() is True
        assert result.has_critical_mismatches() is False
        assert len(result.mismatches) == 0
    
    def test_result_with_mismatches(self) -> None:
        """Result with mismatches returns correct status."""
        from runtime.observation.reconciliation_models import ReconciliationMismatch
        
        result = ReconciliationResult(
            status=ReconciliationStatus.MISMATCHES_FOUND,
            scope_request_id="req-1",
            total_rows_examined=2,
        )
        result.mismatches.append(ReconciliationMismatch(
            classification=MismatchClassification.MISSING_EXECUTION,
            severity=MismatchSeverity.ERROR,
            description="Test mismatch",
            request_id="req-1",
        ))
        
        assert result.is_consistent() is False
        assert len(result.mismatches) == 1
    
    def test_result_summary(self) -> None:
        """ReconciliationResult.summary() produces readable output."""
        result = ReconciliationResult(
            status=ReconciliationStatus.CONSISTENT,
            scope_request_id="req-1",
            total_rows_examined=3,
            decision_rows_found=1,
            execution_rows_found=1,
        )
        
        summary = result.summary()
        
        assert "Reconciliation Status: consistent" in summary
        assert "Rows examined: 3" in summary
        assert "No mismatches found" in summary
    
    def test_result_to_dict(self) -> None:
        """ReconciliationResult.to_dict() produces serializable output."""
        result = ReconciliationResult(
            status=ReconciliationStatus.CONSISTENT,
            scope_request_id="req-1",
            total_rows_examined=2,
        )
        
        d = result.to_dict()
        
        assert d["status"] == "consistent"
        assert d["is_consistent"] is True
        assert "statistics" in d
        assert d["statistics"]["total_rows_examined"] == 2


class TestLedgerReconciliationByRequestId:
    """Test reconciliation by request_id."""
    
    def test_reconcile_consistent_request(self) -> None:
        """Reconcile request with matching decision and execution rows."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="decision-1",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-consistent",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-same",
                    "intent_id": "intent-1",
                    "decision_posture": "safe_execute",
                },
            )
            store.append(
                ledger_row_id="execution-1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-consistent",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-same",
                    "intent_id": "intent-1",
                    "success": True,
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_request_id("req-consistent")
            
            assert result.is_consistent() is True
            assert result.status == ReconciliationStatus.CONSISTENT
            assert result.total_rows_examined == 2
            assert result.decision_rows_found == 1
            assert result.execution_rows_found == 1
    
    def test_reconcile_missing_execution(self) -> None:
        """Detect missing execution row for safe_execute decision."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="decision-only",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-missing-exec",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-orphan",
                    "intent_id": "intent-1",
                    "decision_posture": "safe_execute",
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_request_id("req-missing-exec")
            
            assert result.is_consistent() is False
            assert result.status == ReconciliationStatus.MISMATCHES_FOUND
            
            missing = result.get_mismatches_by_classification(
                MismatchClassification.MISSING_EXECUTION
            )
            assert len(missing) == 1
            assert missing[0].severity == MismatchSeverity.ERROR
    
    def test_reconcile_missing_decision(self) -> None:
        """Detect execution row without matching decision."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="exec-only",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-missing-decision",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-orphan-exec",
                    "success": True,
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_request_id("req-missing-decision")
            
            missing = result.get_mismatches_by_classification(
                MismatchClassification.MISSING_DECISION
            )
            assert len(missing) == 1
    
    def test_reconcile_canonical_hash_mismatch(self) -> None:
        """Detect canonical_hash mismatch between decision and execution."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="decision-1",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-ch-mismatch",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-decision",
                    "decision_posture": "safe_execute",
                },
            )
            store.append(
                ledger_row_id="execution-1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-ch-mismatch",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-execution-different",
                    "success": True,
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_request_id("req-ch-mismatch")
            
            mismatches = result.get_mismatches_by_classification(
                MismatchClassification.CANONICAL_HASH_MISMATCH
            )
            assert len(mismatches) >= 1
    
    def test_reconcile_refused_no_execution_expected(self) -> None:
        """Refused decision should not require execution row."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="refused-1",
                event_type=EVENT_PLANGATE_REFUSED,
                outcome_type="refused",
                request_id="req-refused",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-refused",
                    "decision_posture": "refuse",
                    "reason": "protected_branch",
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_request_id("req-refused")
            
            missing_exec = result.get_mismatches_by_classification(
                MismatchClassification.MISSING_EXECUTION
            )
            assert len(missing_exec) == 0


class TestLedgerReconciliationByCanonicalHash:
    """Test reconciliation by canonical_hash."""
    
    def test_reconcile_by_canonical_hash(self) -> None:
        """Reconcile all rows with same canonical_hash."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="decision-ch",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-1",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-target",
                    "intent_id": "intent-1",
                },
            )
            store.append(
                ledger_row_id="exec-ch",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-1",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-target",
                    "intent_id": "intent-1",
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_canonical_hash("ch-target")
            
            assert result.total_rows_examined == 2
            assert result.scope_canonical_hash == "ch-target"
            assert len(result.linkages) == 2
    
    def test_reconcile_intent_id_mismatch(self) -> None:
        """Detect intent_id mismatch for same canonical_hash."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="decision-1",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-1",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-same",
                    "intent_id": "intent-A",
                },
            )
            store.append(
                ledger_row_id="exec-1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-1",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-same",
                    "intent_id": "intent-B",
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_canonical_hash("ch-same")
            
            mismatches = result.get_mismatches_by_classification(
                MismatchClassification.INTENT_ID_MISMATCH
            )
            assert len(mismatches) == 1


class TestLedgerReconciliationByPlanHash:
    """Test reconciliation by plan_hash."""
    
    def test_reconcile_by_plan_hash(self) -> None:
        """Reconcile all rows with same plan_hash."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="row-ph-1",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-1",
                plan_hash="ph-target",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-1",
                    "plan_hash": "ph-target",
                },
            )
            store.append(
                ledger_row_id="row-ph-2",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-1",
                plan_hash="ph-target",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-1",
                    "plan_hash": "ph-target",
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_plan_hash("ph-target")
            
            assert result.total_rows_examined == 2
            assert result.scope_plan_hash == "ph-target"


class TestLedgerReconciliationAll:
    """Test full ledger reconciliation."""
    
    def test_reconcile_all_consistent(self) -> None:
        """Reconcile all rows in consistent ledger."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            for i in range(3):
                store.append(
                    ledger_row_id=f"decision-{i}",
                    event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                    outcome_type="safe_execute",
                    request_id=f"req-{i}",
                    plan_hash=f"ph-{i}",
                    sandbox_id="",
                    payload={
                        "canonical_hash": f"ch-{i}",
                        "intent_id": f"intent-{i}",
                    },
                )
                store.append(
                    ledger_row_id=f"exec-{i}",
                    event_type=EVENT_EXECUTED,
                    outcome_type="executed",
                    request_id=f"req-{i}",
                    plan_hash=f"ph-{i}",
                    sandbox_id="",
                    payload={
                        "canonical_hash": f"ch-{i}",
                        "intent_id": f"intent-{i}",
                    },
                )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_all()
            
            assert result.total_rows_examined == 6
            assert result.decision_rows_found == 3
            assert result.execution_rows_found == 3
            assert result.is_consistent() is True
    
    def test_reconcile_all_with_legacy_rows(self) -> None:
        """Reconcile ledger with legacy rows (no canonical_hash)."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="legacy-exec",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-legacy",
                plan_hash="ph-legacy",
                sandbox_id="",
                payload={
                    "success": True,
                },
            )
            
            store.append(
                ledger_row_id="modern-decision",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-modern",
                plan_hash="ph-modern",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-modern",
                    "intent_id": "intent-modern",
                },
            )
            store.append(
                ledger_row_id="modern-exec",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-modern",
                plan_hash="ph-modern",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-modern",
                    "intent_id": "intent-modern",
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_all()
            
            assert result.total_rows_examined == 3
            assert result.legacy_rows_found >= 1
            
            legacy_mismatches = result.get_mismatches_by_classification(
                MismatchClassification.LEGACY_ROW_NO_IDENTITY
            )
            assert len(legacy_mismatches) >= 1
            assert legacy_mismatches[0].severity == MismatchSeverity.INFO


class TestReplayLinkageReconciliation:
    """Test replay linkage reconciliation."""
    
    def test_reconcile_replay_linkage(self) -> None:
        """Verify replay execution is linked to original."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="original-decision",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-original",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-original",
                    "intent_id": "intent-1",
                },
            )
            store.append(
                ledger_row_id="original-exec",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-original",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-original",
                    "intent_id": "intent-1",
                },
            )
            
            store.append(
                ledger_row_id="replay-exec",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-replay",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-original",
                    "execution_surface": "replay",
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_replay_linkage("ch-original", "req-replay")
            
            assert result.execution_rows_found == 3
            assert result.replay_rows_found == 1
    
    def test_reconcile_replay_missing_surface(self) -> None:
        """Detect replay execution missing execution_surface=replay."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="original-exec",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-original",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-original",
                },
            )
            
            store.append(
                ledger_row_id="replay-exec",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-replay",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-original",
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_replay_linkage("ch-original", "req-replay")
            
            mismatches = result.get_mismatches_by_classification(
                MismatchClassification.MISSING_REPLAY_LINK
            )
            assert len(mismatches) == 1


class TestDuplicateDetection:
    """Test duplicate decision/execution detection."""
    
    def test_detect_duplicate_decisions(self) -> None:
        """Detect multiple decision rows for same canonical_hash."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            for i in range(2):
                store.append(
                    ledger_row_id=f"decision-dup-{i}",
                    event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                    outcome_type="safe_execute",
                    request_id="req-dup",
                    plan_hash="ph-1",
                    sandbox_id="",
                    payload={
                        "canonical_hash": "ch-dup",
                        "intent_id": f"intent-{i}",
                    },
                )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_request_id("req-dup")
            
            dups = result.get_mismatches_by_classification(
                MismatchClassification.DUPLICATE_DECISION
            )
            assert len(dups) == 1
    
    def test_detect_duplicate_executions(self) -> None:
        """Detect multiple execution rows for same canonical_hash."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="decision-1",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-dup-exec",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-dup-exec",
                },
            )
            
            for i in range(2):
                store.append(
                    ledger_row_id=f"exec-dup-{i}",
                    event_type=EVENT_EXECUTED,
                    outcome_type="executed",
                    request_id="req-dup-exec",
                    plan_hash="ph-1",
                    sandbox_id="",
                    payload={
                        "canonical_hash": "ch-dup-exec",
                    },
                )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_request_id("req-dup-exec")
            
            dups = result.get_mismatches_by_classification(
                MismatchClassification.DUPLICATE_EXECUTION
            )
            assert len(dups) == 1


class TestReconciliationConfig:
    """Test reconciliation configuration."""
    
    def test_config_disable_execution_requirement(self) -> None:
        """Disable execution requirement for safe_execute."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="decision-only",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-config",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-config",
                },
            )
            
            config = ReconciliationConfig(require_execution_for_safe_execute=False)
            service = LedgerReconciliationService(store, config=config)
            result = service.reconcile_by_request_id("req-config")
            
            missing = result.get_mismatches_by_classification(
                MismatchClassification.MISSING_EXECUTION
            )
            assert len(missing) == 0
    
    def test_config_disable_legacy_warnings(self) -> None:
        """Disable legacy row warnings."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="legacy-1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-legacy",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "success": True,
                },
            )
            
            config = ReconciliationConfig(treat_legacy_as_warning=False)
            service = LedgerReconciliationService(store, config=config)
            result = service.reconcile_by_request_id("req-legacy")
            
            legacy = result.get_mismatches_by_classification(
                MismatchClassification.LEGACY_ROW_NO_IDENTITY
            )
            assert len(legacy) == 0


class TestMismatchClassificationDeterminism:
    """Test that mismatch classifications are deterministic."""
    
    def test_same_input_same_classification(self) -> None:
        """Same ledger state produces same mismatches."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="decision-det",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-det",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-det",
                },
            )
            
            service = LedgerReconciliationService(store)
            
            result1 = service.reconcile_by_request_id("req-det")
            result2 = service.reconcile_by_request_id("req-det")
            
            assert len(result1.mismatches) == len(result2.mismatches)
            assert result1.status == result2.status
            
            for m1, m2 in zip(result1.mismatches, result2.mismatches):
                assert m1.classification == m2.classification
                assert m1.severity == m2.severity
    
    def test_classification_enum_values(self) -> None:
        """MismatchClassification enum has expected values."""
        expected = [
            "missing_decision",
            "missing_execution",
            "missing_replay_link",
            "canonical_hash_mismatch",
            "plan_hash_mismatch",
            "request_id_orphan",
            "intent_id_mismatch",
            "duplicate_decision",
            "duplicate_execution",
            "boundary_phrase_inconsistent",
            "invariant_violation",
            "legacy_row_no_identity",
        ]
        
        actual = [c.value for c in MismatchClassification]
        
        for exp in expected:
            assert exp in actual


class TestBackwardCompatibility:
    """Test backward compatibility with older ledger rows."""
    
    def test_mixed_legacy_and_modern_rows(self) -> None:
        """Reconcile ledger with mixed legacy and modern rows."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="legacy-1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-mixed-1",
                plan_hash="ph-1",
                sandbox_id="",
                payload={
                    "success": True,
                    "command": ["echo", "legacy"],
                },
            )
            
            store.append(
                ledger_row_id="modern-decision",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-mixed-2",
                plan_hash="ph-2",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-modern",
                    "intent_id": "intent-modern",
                    "decision_posture": "safe_execute",
                },
            )
            store.append(
                ledger_row_id="modern-exec",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-mixed-2",
                plan_hash="ph-2",
                sandbox_id="",
                payload={
                    "canonical_hash": "ch-modern",
                    "intent_id": "intent-modern",
                    "success": True,
                },
            )
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_all()
            
            assert result.total_rows_examined == 3
            assert result.legacy_rows_found >= 1
            
            modern_result = service.reconcile_by_request_id("req-mixed-2")
            assert modern_result.is_consistent() is True
    
    def test_empty_ledger(self) -> None:
        """Handle empty ledger gracefully."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db")
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_all()
            
            assert result.total_rows_examined == 0
            assert result.is_consistent() is True
    
    def test_nonexistent_request_id(self) -> None:
        """Handle nonexistent request_id gracefully."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db")
            
            service = LedgerReconciliationService(store)
            result = service.reconcile_by_request_id("nonexistent")
            
            assert result.total_rows_examined == 0
            assert result.is_consistent() is True
