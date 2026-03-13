"""
Ledger Completeness Tests — M3.5 Ledger Completeness and Replay.

Tests verify:
1. Append-only enforcement (no mutation/delete)
2. Deterministic event_id and plan_hash linkage
3. Replay of traced runtime sessions
4. No duplicate ledger emission for REF refusal
5. Invalid ledger combinations rejected
6. Plan-hash linkage
7. Sandbox execution ledger row
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from runtime.ledger.contracts import (
    AuthorityVerdict,
    BoundaryVerdict,
    ExecutionIntent,
    LedgerEventType,
    LedgerRowV1,
    PhaseEmitted,
    ReplaySession,
    TerminalPosture,
    ToolCallAttempt,
)
from runtime.ledger.emitter import (
    LedgerEmitterV1,
    compute_boundary_phrase_hash,
    compute_plan_hash,
)
from runtime.ledger.replay import LedgerReplay, ReconciliationResult
from runtime.ledger.store import LedgerStore, LedgerStoreError


class TestLedgerRowContract:
    """Test LedgerRowV1 data contract and invariant validation."""

    def test_ledger_row_to_dict_schema_compliant(self) -> None:
        """LedgerRowV1.to_dict() produces ledger_row.v0.1 schema-compliant output."""
        row = LedgerRowV1(
            event_id="ldg-abc123",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req-001",
            session_id="sess-001",
            mode="shadow",
            runtime_version="0.1.0",
            plan_hash="abc" * 21 + "a",
            plan_schema_version="plan.v0.1",
            phase_emitted="REF",
            terminal_posture="refuse",
            authority_verdict="fail",
            boundary_verdict="blocked",
            ref_enforced=True,
            irreversible_boundary_phrase="merge to production",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=["MISSING_AUTHORITY", "REF_ENFORCED"],
        )
        
        d = row.to_dict()
        
        assert d["schema_version"] == "ledger_row.v0.1"
        assert "event" in d
        assert d["event"]["event_id"] == "ldg-abc123"
        assert d["event"]["request_id"] == "req-001"
        assert d["event"]["mode"] == "shadow"
        assert "plan_link" in d
        assert d["plan_link"]["plan_hash"] == "abc" * 21 + "a"
        assert "verdicts" in d
        assert d["verdicts"]["phase_emitted"] == "REF"
        assert d["verdicts"]["terminal_posture"] == "refuse"
        assert d["verdicts"]["ref_enforced"] is True
        assert "boundary" in d
        assert d["boundary"]["irreversible_boundary_phrase"] == "merge to production"
        assert "actions" in d
        assert "reason_codes" in d

    def test_ledger_row_roundtrip(self) -> None:
        """LedgerRowV1 survives to_dict/from_dict roundtrip."""
        original = LedgerRowV1(
            event_id="ldg-test",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req-rt",
            session_id="sess-rt",
            mode="live",
            runtime_version="0.2.0",
            plan_hash="x" * 64,
            plan_schema_version="plan.v0.1",
            phase_emitted="CONF",
            terminal_posture="bounded_allow",
            authority_verdict="pass",
            boundary_verdict="allowed_pre_boundary_only",
            ref_enforced=False,
            irreversible_boundary_phrase="deploy to staging",
            boundary_cross_attempted=True,
            boundary_crossed=False,
            reason_codes=["SAFE_PREBOUNDARY_ONLY"],
            tool_calls_attempted=[
                ToolCallAttempt(tool="git", intent="commit", blocked=False, reason_code=""),
            ],
            execution_intents=[
                ExecutionIntent(intent="echo hello", blocked=False, reason_code=""),
            ],
            latency_ms=150,
        )
        
        d = original.to_dict()
        restored = LedgerRowV1.from_dict(d)
        
        assert restored.event_id == original.event_id
        assert restored.request_id == original.request_id
        assert restored.phase_emitted == original.phase_emitted
        assert restored.terminal_posture == original.terminal_posture
        assert restored.latency_ms == original.latency_ms
        assert len(restored.tool_calls_attempted) == 1
        assert len(restored.execution_intents) == 1

    def test_invariant_l1_ref_enforced_requires_ref_or_mix(self) -> None:
        """L1: If ref_enforced=true, phase_emitted must be REF or MIX."""
        row = LedgerRowV1(
            event_id="test",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req",
            session_id="sess",
            mode="shadow",
            runtime_version="0.1.0",
            plan_hash="x" * 64,
            plan_schema_version="plan.v0.1",
            phase_emitted="CONF",
            terminal_posture="refuse",
            authority_verdict="fail",
            boundary_verdict="blocked",
            ref_enforced=True,
            irreversible_boundary_phrase="",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=[],
        )
        
        violations = row.validate_invariants()
        assert "L1" in violations

    def test_invariant_l2_crossed_requires_crossed_verdict(self) -> None:
        """L2: If boundary_crossed=true, boundary_verdict must be 'crossed'."""
        row = LedgerRowV1(
            event_id="test",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req",
            session_id="sess",
            mode="shadow",
            runtime_version="0.1.0",
            plan_hash="x" * 64,
            plan_schema_version="plan.v0.1",
            phase_emitted="CODE",
            terminal_posture="safe_execute",
            authority_verdict="pass",
            boundary_verdict="not_reached",
            ref_enforced=False,
            irreversible_boundary_phrase="",
            boundary_cross_attempted=False,
            boundary_crossed=True,
            reason_codes=[],
        )
        
        violations = row.validate_invariants()
        assert "L2" in violations

    def test_invariant_l3_attempted_not_crossed_requires_blocked(self) -> None:
        """L3: If attempted but not crossed, boundary_verdict must be 'blocked'."""
        row = LedgerRowV1(
            event_id="test",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req",
            session_id="sess",
            mode="shadow",
            runtime_version="0.1.0",
            plan_hash="x" * 64,
            plan_schema_version="plan.v0.1",
            phase_emitted="CONF",
            terminal_posture="bounded_allow",
            authority_verdict="pass",
            boundary_verdict="not_reached",
            ref_enforced=False,
            irreversible_boundary_phrase="",
            boundary_cross_attempted=True,
            boundary_crossed=False,
            reason_codes=[],
        )
        
        violations = row.validate_invariants()
        assert "L3" in violations

    def test_invariant_l4_authority_fail_cannot_cross(self) -> None:
        """L4: authority_verdict != pass AND boundary_verdict == crossed is INVALID."""
        row = LedgerRowV1(
            event_id="test",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req",
            session_id="sess",
            mode="shadow",
            runtime_version="0.1.0",
            plan_hash="x" * 64,
            plan_schema_version="plan.v0.1",
            phase_emitted="CODE",
            terminal_posture="safe_execute",
            authority_verdict="fail",
            boundary_verdict="crossed",
            ref_enforced=False,
            irreversible_boundary_phrase="",
            boundary_cross_attempted=True,
            boundary_crossed=True,
            reason_codes=[],
        )
        
        violations = row.validate_invariants()
        assert "L4" in violations

    def test_valid_row_no_violations(self) -> None:
        """Valid ledger row has no invariant violations."""
        row = LedgerRowV1(
            event_id="test",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req",
            session_id="sess",
            mode="shadow",
            runtime_version="0.1.0",
            plan_hash="x" * 64,
            plan_schema_version="plan.v0.1",
            phase_emitted="REF",
            terminal_posture="refuse",
            authority_verdict="fail",
            boundary_verdict="blocked",
            ref_enforced=True,
            irreversible_boundary_phrase="deploy to prod",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=["MISSING_AUTHORITY"],
        )
        
        violations = row.validate_invariants()
        assert len(violations) == 0


class TestLedgerStore:
    """Test LedgerStore append-only persistence."""

    def test_append_and_retrieve_by_event_id(self) -> None:
        """Append and retrieve ledger row by event_id."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db", fixed_time="2026-03-13T10:00:00Z")
            
            row = LedgerRowV1(
                event_id="ldg-test-001",
                timestamp_utc="2026-03-13T10:00:00Z",
                request_id="req-001",
                session_id="sess-001",
                mode="shadow",
                runtime_version="0.1.0",
                plan_hash="abc123",
                plan_schema_version="plan.v0.1",
                phase_emitted="REF",
                terminal_posture="refuse",
                authority_verdict="fail",
                boundary_verdict="blocked",
                ref_enforced=True,
                irreversible_boundary_phrase="",
                boundary_cross_attempted=False,
                boundary_crossed=False,
                reason_codes=["MISSING_AUTHORITY"],
            )
            
            event_id = store.append_row(row, LedgerEventType.DECISION_EMITTED)
            assert event_id == "ldg-test-001"
            
            retrieved = store.get_by_event_id("ldg-test-001")
            assert retrieved is not None
            assert retrieved.request_id == "req-001"
            assert retrieved.phase_emitted == "REF"

    def test_append_duplicate_raises_error(self) -> None:
        """Appending duplicate event_id raises LedgerStoreError (append-only enforcement)."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            
            row = LedgerRowV1(
                event_id="ldg-dup",
                timestamp_utc="2026-03-13T10:00:00Z",
                request_id="req",
                session_id="sess",
                mode="shadow",
                runtime_version="0.1.0",
                plan_hash="x",
                plan_schema_version="plan.v0.1",
                phase_emitted="REF",
                terminal_posture="refuse",
                authority_verdict="fail",
                boundary_verdict="blocked",
                ref_enforced=True,
                irreversible_boundary_phrase="",
                boundary_cross_attempted=False,
                boundary_crossed=False,
                reason_codes=[],
            )
            
            store.append_row(row, LedgerEventType.DECISION_EMITTED)
            
            with pytest.raises(LedgerStoreError) as exc_info:
                store.append_row(row, LedgerEventType.DECISION_EMITTED)
            assert "Duplicate event_id" in str(exc_info.value)

    def test_get_by_request_id(self) -> None:
        """Retrieve all rows for a request_id."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            
            for i in range(3):
                row = LedgerRowV1(
                    event_id=f"ldg-{i}",
                    timestamp_utc=f"2026-03-13T10:0{i}:00Z",
                    request_id="req-multi",
                    session_id="sess",
                    mode="shadow",
                    runtime_version="0.1.0",
                    plan_hash="x",
                    plan_schema_version="plan.v0.1",
                    phase_emitted="CODE",
                    terminal_posture="safe_execute",
                    authority_verdict="pass",
                    boundary_verdict="not_reached",
                    ref_enforced=False,
                    irreversible_boundary_phrase="",
                    boundary_cross_attempted=False,
                    boundary_crossed=False,
                    reason_codes=[],
                )
                store.append_row(row, LedgerEventType.TRANSITION_APPLIED)
            
            rows = store.get_by_request_id("req-multi")
            assert len(rows) == 3

    def test_get_by_join_key(self) -> None:
        """Retrieve by join key (request_id, plan_hash)."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            
            row1 = LedgerRowV1(
                event_id="ldg-j1",
                timestamp_utc="2026-03-13T10:00:00Z",
                request_id="req-join",
                session_id="sess",
                mode="shadow",
                runtime_version="0.1.0",
                plan_hash="plan-abc",
                plan_schema_version="plan.v0.1",
                phase_emitted="REF",
                terminal_posture="refuse",
                authority_verdict="fail",
                boundary_verdict="blocked",
                ref_enforced=True,
                irreversible_boundary_phrase="",
                boundary_cross_attempted=False,
                boundary_crossed=False,
                reason_codes=[],
            )
            store.append_row(row1, LedgerEventType.DECISION_EMITTED)
            
            row2 = LedgerRowV1(
                event_id="ldg-j2",
                timestamp_utc="2026-03-13T10:01:00Z",
                request_id="req-join",
                session_id="sess",
                mode="shadow",
                runtime_version="0.1.0",
                plan_hash="plan-xyz",
                plan_schema_version="plan.v0.1",
                phase_emitted="CONF",
                terminal_posture="bounded_allow",
                authority_verdict="pass",
                boundary_verdict="allowed_pre_boundary_only",
                ref_enforced=False,
                irreversible_boundary_phrase="",
                boundary_cross_attempted=True,
                boundary_crossed=False,
                reason_codes=[],
            )
            store.append_row(row2, LedgerEventType.DECISION_EMITTED)
            
            rows_abc = store.get_by_join_key("req-join", "plan-abc")
            assert len(rows_abc) == 1
            assert rows_abc[0].event_id == "ldg-j1"
            
            rows_xyz = store.get_by_join_key("req-join", "plan-xyz")
            assert len(rows_xyz) == 1
            assert rows_xyz[0].event_id == "ldg-j2"


class TestDeterministicHashing:
    """Test deterministic hash generation for plan and event_id."""

    def test_same_plan_produces_same_hash(self) -> None:
        """Identical plan objects produce identical plan_hash."""
        plan = {
            "request_id": "req-123",
            "action_type": "commit",
            "boundary_phrase": "deploy to prod",
        }
        
        hash1 = compute_plan_hash(plan)
        hash2 = compute_plan_hash(plan)
        
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_different_plans_produce_different_hashes(self) -> None:
        """Different plan objects produce different plan_hash."""
        plan1 = {"request_id": "req-001", "action": "commit"}
        plan2 = {"request_id": "req-002", "action": "commit"}
        
        hash1 = compute_plan_hash(plan1)
        hash2 = compute_plan_hash(plan2)
        
        assert hash1 != hash2

    def test_boundary_phrase_hash_deterministic(self) -> None:
        """Boundary phrase hash is deterministic."""
        phrase = "merge to production branch"
        
        hash1 = compute_boundary_phrase_hash(phrase)
        hash2 = compute_boundary_phrase_hash(phrase)
        
        assert hash1 == hash2

    def test_emitter_produces_deterministic_event_id(self) -> None:
        """LedgerEmitterV1 produces deterministic event_id for same inputs."""
        emitter1 = LedgerEmitterV1(fixed_time="2026-03-13T10:00:00Z")
        emitter2 = LedgerEmitterV1(fixed_time="2026-03-13T10:00:00Z")
        
        plan = {"request_id": "req-det", "action": "test"}
        
        row1 = emitter1.emit_decision(
            request_id="req-det",
            session_id="sess-det",
            plan=plan,
            phase_emitted="DES",
            terminal_posture="safe_execute",
            authority_verdict="pass",
            boundary_verdict="not_reached",
            ref_enforced=False,
            irreversible_boundary_phrase="",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=[],
        )
        
        row2 = emitter2.emit_decision(
            request_id="req-det",
            session_id="sess-det",
            plan=plan,
            phase_emitted="DES",
            terminal_posture="safe_execute",
            authority_verdict="pass",
            boundary_verdict="not_reached",
            ref_enforced=False,
            irreversible_boundary_phrase="",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=[],
        )
        
        assert row1.event_id == row2.event_id
        assert row1.plan_hash == row2.plan_hash


class TestLedgerEmitter:
    """Test LedgerEmitterV1 emission and validation."""

    def test_emit_decision_creates_valid_row(self) -> None:
        """emit_decision creates schema-compliant row."""
        emitter = LedgerEmitterV1(fixed_time="2026-03-13T10:00:00Z")
        
        plan = {"request_id": "req-001", "action": "safe_commit"}
        
        row = emitter.emit_decision(
            request_id="req-001",
            session_id="sess-001",
            plan=plan,
            phase_emitted=PhaseEmitted.DES,
            terminal_posture=TerminalPosture.SAFE_EXECUTE,
            authority_verdict=AuthorityVerdict.PASS,
            boundary_verdict=BoundaryVerdict.NOT_REACHED,
            ref_enforced=False,
            irreversible_boundary_phrase="",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=[],
        )
        
        assert row.event_id.startswith("ldg-")
        assert row.request_id == "req-001"
        assert row.phase_emitted == "DES"
        assert row.terminal_posture == "safe_execute"
        assert len(row.validate_invariants()) == 0

    def test_emit_decision_rejects_invalid_combination(self) -> None:
        """emit_decision raises on invalid invariant combination."""
        emitter = LedgerEmitterV1(fixed_time="2026-03-13T10:00:00Z")
        
        plan = {"request_id": "req-invalid"}
        
        with pytest.raises(ValueError) as exc_info:
            emitter.emit_decision(
                request_id="req-invalid",
                session_id="sess",
                plan=plan,
                phase_emitted="CONF",
                terminal_posture="safe_execute",
                authority_verdict="fail",
                boundary_verdict="crossed",
                ref_enforced=False,
                irreversible_boundary_phrase="",
                boundary_cross_attempted=True,
                boundary_crossed=True,
                reason_codes=[],
            )
        
        assert "invariant violations" in str(exc_info.value).lower()

    def test_emit_with_store_persists(self) -> None:
        """emit_decision with store persists to database."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            emitter = LedgerEmitterV1(store=store, fixed_time="2026-03-13T10:00:00Z")
            
            plan = {"request_id": "req-persist"}
            
            row = emitter.emit_decision(
                request_id="req-persist",
                session_id="sess",
                plan=plan,
                phase_emitted="REF",
                terminal_posture="refuse",
                authority_verdict="fail",
                boundary_verdict="blocked",
                ref_enforced=True,
                irreversible_boundary_phrase="merge to main",
                boundary_cross_attempted=False,
                boundary_crossed=False,
                reason_codes=["MISSING_AUTHORITY"],
            )
            
            retrieved = store.get_by_event_id(row.event_id)
            assert retrieved is not None
            assert retrieved.request_id == "req-persist"

    def test_emit_execution_creates_code_phase_row(self) -> None:
        """emit_execution creates CODE phase ledger row."""
        emitter = LedgerEmitterV1(fixed_time="2026-03-13T10:00:00Z")
        
        row = emitter.emit_execution(
            request_id="req-exec",
            session_id="sess",
            plan_hash="x" * 64,
            sandbox_id="sbx-001",
            outcome="executed",
            commands_executed=["echo hello"],
            commands_blocked=[],
            exit_code=0,
            duration_ms=100,
            artifacts=["out.txt"],
        )
        
        assert row.phase_emitted == "CODE"
        assert row.terminal_posture == "safe_execute"
        assert len(row.execution_intents) == 1


class TestLedgerReplay:
    """Test LedgerReplay session reconstruction and reconciliation."""

    def test_reconstruct_session(self) -> None:
        """reconstruct_session returns complete session from ledger rows."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            emitter = LedgerEmitterV1(store=store, fixed_time="2026-03-13T10:00:00Z")
            
            plan = {"request_id": "req-replay"}
            
            emitter.emit_decision(
                request_id="req-replay",
                session_id="sess-replay",
                plan=plan,
                phase_emitted="DES",
                terminal_posture="safe_execute",
                authority_verdict="pass",
                boundary_verdict="not_reached",
                ref_enforced=False,
                irreversible_boundary_phrase="",
                boundary_cross_attempted=False,
                boundary_crossed=False,
                reason_codes=[],
            )
            
            replay = LedgerReplay(store)
            session = replay.reconstruct_session("req-replay")
            
            assert session.request_id == "req-replay"
            assert session.session_id == "sess-replay"
            assert len(session.ledger_rows) == 1
            assert session.decision_event is not None

    def test_reconcile_by_join_key(self) -> None:
        """reconcile returns ReconciliationResult for join key."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            emitter = LedgerEmitterV1(store=store, fixed_time="2026-03-13T10:00:00Z")
            
            plan = {"request_id": "req-rec", "action": "test"}
            plan_hash = compute_plan_hash(plan)
            
            emitter.emit_decision(
                request_id="req-rec",
                session_id="sess-rec",
                plan=plan,
                phase_emitted="CONF",
                terminal_posture="bounded_allow",
                authority_verdict="pass",
                boundary_verdict="allowed_pre_boundary_only",
                ref_enforced=False,
                irreversible_boundary_phrase="deploy to staging",
                boundary_cross_attempted=False,
                boundary_crossed=False,
                reason_codes=["SAFE_PREBOUNDARY_ONLY"],
            )
            
            replay = LedgerReplay(store)
            result = replay.reconcile("req-rec", plan_hash)
            
            assert result.request_id == "req-rec"
            assert result.plan_hash == plan_hash
            assert len(result.rows) == 1
            assert result.is_valid()

    def test_validate_no_duplicate_emissions_ref_refusal(self) -> None:
        """Simple REF refusal produces exactly one ledger row."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            emitter = LedgerEmitterV1(store=store, fixed_time="2026-03-13T10:00:00Z")
            
            plan = {"request_id": "req-single-ref"}
            
            emitter.emit_decision(
                request_id="req-single-ref",
                session_id="sess",
                plan=plan,
                phase_emitted="REF",
                terminal_posture="refuse",
                authority_verdict="fail",
                boundary_verdict="blocked",
                ref_enforced=True,
                irreversible_boundary_phrase="merge without approval",
                boundary_cross_attempted=False,
                boundary_crossed=False,
                reason_codes=["MISSING_AUTHORITY", "REF_ENFORCED"],
            )
            
            replay = LedgerReplay(store)
            errors = replay.validate_no_duplicate_emissions("req-single-ref")
            
            assert len(errors) == 0

    def test_detect_duplicate_ref_refusal_emissions(self) -> None:
        """Detect multiple REF refusal emissions for same request."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            
            for i in range(2):
                row = LedgerRowV1(
                    event_id=f"ldg-dup-ref-{i}",
                    timestamp_utc=f"2026-03-13T10:0{i}:00Z",
                    request_id="req-dup-ref",
                    session_id="sess",
                    mode="shadow",
                    runtime_version="0.1.0",
                    plan_hash="x" * 64,
                    plan_schema_version="plan.v0.1",
                    phase_emitted="REF",
                    terminal_posture="refuse",
                    authority_verdict="fail",
                    boundary_verdict="blocked",
                    ref_enforced=True,
                    irreversible_boundary_phrase="",
                    boundary_cross_attempted=False,
                    boundary_crossed=False,
                    reason_codes=["MISSING_AUTHORITY"],
                )
                store.append_row(row, LedgerEventType.DECISION_EMITTED)
            
            replay = LedgerReplay(store)
            errors = replay.validate_no_duplicate_emissions("req-dup-ref")
            
            assert len(errors) > 0
            assert "Multiple REF refusal" in errors[0]

    def test_get_session_timeline(self) -> None:
        """get_session_timeline returns chronological events."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            emitter = LedgerEmitterV1(store=store)
            
            plan = {"request_id": "req-timeline"}
            
            emitter.emit_decision(
                request_id="req-timeline",
                session_id="sess",
                plan=plan,
                phase_emitted="DES",
                terminal_posture="safe_execute",
                authority_verdict="pass",
                boundary_verdict="not_reached",
                ref_enforced=False,
                irreversible_boundary_phrase="",
                boundary_cross_attempted=False,
                boundary_crossed=False,
                reason_codes=[],
            )
            
            replay = LedgerReplay(store)
            timeline = replay.get_session_timeline("req-timeline")
            
            assert len(timeline) == 1
            assert "timestamp_utc" in timeline[0]
            assert timeline[0]["phase"] == "DES"


class TestPlanHashLinkage:
    """Test plan_hash linkage between plan and ledger."""

    def test_ledger_row_contains_plan_hash(self) -> None:
        """Ledger row contains plan_hash for join."""
        emitter = LedgerEmitterV1(fixed_time="2026-03-13T10:00:00Z")
        
        plan = {"request_id": "req-link", "action": "deploy"}
        expected_hash = compute_plan_hash(plan)
        
        row = emitter.emit_decision(
            request_id="req-link",
            session_id="sess",
            plan=plan,
            phase_emitted="CONF",
            terminal_posture="bounded_allow",
            authority_verdict="pass",
            boundary_verdict="allowed_pre_boundary_only",
            ref_enforced=False,
            irreversible_boundary_phrase="",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=[],
        )
        
        assert row.plan_hash == expected_hash
        
        d = row.to_dict()
        assert d["plan_link"]["plan_hash"] == expected_hash

    def test_join_by_request_id_and_plan_hash(self) -> None:
        """Join key (request_id, plan_hash) links related records."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            emitter = LedgerEmitterV1(store=store, fixed_time="2026-03-13T10:00:00Z")
            
            plan1 = {"request_id": "req-join-test", "action": "commit"}
            plan2 = {"request_id": "req-join-test", "action": "push"}
            
            row1 = emitter.emit_decision(
                request_id="req-join-test",
                session_id="sess",
                plan=plan1,
                phase_emitted="DES",
                terminal_posture="safe_execute",
                authority_verdict="pass",
                boundary_verdict="not_reached",
                ref_enforced=False,
                irreversible_boundary_phrase="",
                boundary_cross_attempted=False,
                boundary_crossed=False,
                reason_codes=[],
            )
            
            emitter2 = LedgerEmitterV1(store=store, fixed_time="2026-03-13T10:01:00Z")
            row2 = emitter2.emit_decision(
                request_id="req-join-test",
                session_id="sess",
                plan=plan2,
                phase_emitted="CONF",
                terminal_posture="bounded_allow",
                authority_verdict="pass",
                boundary_verdict="allowed_pre_boundary_only",
                ref_enforced=False,
                irreversible_boundary_phrase="",
                boundary_cross_attempted=False,
                boundary_crossed=False,
                reason_codes=[],
            )
            
            rows_plan1 = store.get_by_join_key("req-join-test", row1.plan_hash)
            rows_plan2 = store.get_by_join_key("req-join-test", row2.plan_hash)
            
            assert len(rows_plan1) == 1
            assert len(rows_plan2) == 1
            assert rows_plan1[0].event_id != rows_plan2[0].event_id


class TestSandboxExecutionLedger:
    """Test sandbox execution ledger row emission."""

    def test_sandbox_executed_produces_ledger_row(self) -> None:
        """Sandbox execution produces CODE phase ledger row."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            emitter = LedgerEmitterV1(store=store, fixed_time="2026-03-13T10:00:00Z")
            
            row = emitter.emit_execution(
                request_id="req-sbx",
                session_id="sess-sbx",
                plan_hash="plan-hash-123",
                sandbox_id="sbx-001",
                outcome="executed",
                commands_executed=["echo hello", "ls -la"],
                commands_blocked=[],
                exit_code=0,
                duration_ms=250,
                artifacts=["output.txt"],
            )
            
            assert row.phase_emitted == "CODE"
            assert row.terminal_posture == "safe_execute"
            assert row.authority_verdict == "pass"
            assert len(row.execution_intents) == 2
            assert row.latency_ms == 250
            
            retrieved = store.get_by_event_id(row.event_id)
            assert retrieved is not None

    def test_sandbox_blocked_produces_ledger_row(self) -> None:
        """Sandbox blocked produces appropriate ledger row."""
        emitter = LedgerEmitterV1(fixed_time="2026-03-13T10:00:00Z")
        
        row = emitter.emit_execution(
            request_id="req-blocked",
            session_id="sess",
            plan_hash="plan-123",
            sandbox_id="sbx-002",
            outcome="blocked",
            commands_executed=[],
            commands_blocked=["curl http://external.com"],
            exit_code=None,
            duration_ms=0,
            artifacts=[],
        )
        
        assert row.terminal_posture == "bounded_allow"
        assert row.boundary_verdict == "blocked"
        assert len(row.execution_intents) == 1
        assert row.execution_intents[0].blocked is True


class TestAppendOnlyEnforcement:
    """Test append-only ledger semantics."""

    def test_no_delete_method_exists(self) -> None:
        """LedgerStore has no delete method."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            
            assert not hasattr(store, "delete")
            assert not hasattr(store, "remove")
            assert not hasattr(store, "drop")

    def test_no_update_method_exists(self) -> None:
        """LedgerStore has no update method."""
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(Path(tmp) / "ledger.db")
            
            assert not hasattr(store, "update")
            assert not hasattr(store, "modify")
            assert not hasattr(store, "edit")

    def test_ledger_row_is_immutable_after_creation(self) -> None:
        """LedgerRowV1 fields should not be mutated after emission."""
        row = LedgerRowV1(
            event_id="ldg-immutable",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req",
            session_id="sess",
            mode="shadow",
            runtime_version="0.1.0",
            plan_hash="x" * 64,
            plan_schema_version="plan.v0.1",
            phase_emitted="REF",
            terminal_posture="refuse",
            authority_verdict="fail",
            boundary_verdict="blocked",
            ref_enforced=True,
            irreversible_boundary_phrase="",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=["MISSING_AUTHORITY"],
        )
        
        d1 = row.to_dict()
        d2 = row.to_dict()
        
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestReplaySession:
    """Test ReplaySession contract."""

    def test_replay_session_completeness_check(self) -> None:
        """ReplaySession.is_complete() requires plan + decision."""
        session = ReplaySession(
            request_id="req",
            session_id="sess",
            plan_hash="x",
        )
        
        assert not session.is_complete()
        
        from runtime.ledger.contracts import PlanEvent, DecisionEvent
        
        session.plan_event = PlanEvent(
            request_id="req",
            session_id="sess",
            plan_hash="x",
            timestamp_utc="2026-03-13T10:00:00Z",
            constitutional_phase_expected="DES",
            boundary_phrase="",
            authority_verdict="pass",
            terminal_posture="safe_execute",
        )
        
        assert not session.is_complete()
        
        session.decision_event = DecisionEvent(
            request_id="req",
            session_id="sess",
            plan_hash="x",
            timestamp_utc="2026-03-13T10:00:00Z",
            decision_posture="safe_execute",
            phase_emitted="DES",
            authority_verdict="pass",
            boundary_verdict="not_reached",
            boundary_crossed=False,
            reason_codes=[],
        )
        
        assert session.is_complete()

    def test_replay_session_to_dict(self) -> None:
        """ReplaySession.to_dict() produces serializable output."""
        session = ReplaySession(
            request_id="req-serial",
            session_id="sess-serial",
            plan_hash="abc123",
        )
        
        d = session.to_dict()
        
        assert d["request_id"] == "req-serial"
        assert d["session_id"] == "sess-serial"
        assert "is_complete" in d
        assert "has_execution" in d
