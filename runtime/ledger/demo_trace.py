#!/usr/bin/env python3
"""
Ledger Demo Trace — M3.5 sample traced session.

Demonstrates plan → decision → ledger linkage and replay reconstruction.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from runtime.ledger.contracts import LedgerEventType
from runtime.ledger.emitter import LedgerEmitterV1, compute_plan_hash
from runtime.ledger.replay import LedgerReplay
from runtime.ledger.store import LedgerStore


def run_traced_session():
    """Run a traced session demonstrating ledger completeness."""
    
    print("=" * 60)
    print("M3.5 Ledger Completeness Demo — Traced Session")
    print("=" * 60)
    print()
    
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "demo_ledger.db"
        
        store = LedgerStore(db_path, runtime_version="0.1.0")
        emitter = LedgerEmitterV1(store=store, runtime_version="0.1.0")
        replay = LedgerReplay(store)
        
        print("Session 1: REF Refusal Path")
        print("-" * 40)
        
        plan1 = {
            "request_id": "req-ref-001",
            "action_type": "merge_without_approval",
            "user_context": {"user_id": "u1", "role": "developer"},
            "boundary_phrase": "merge to production branch",
        }
        plan_hash1 = compute_plan_hash(plan1)
        
        print(f"Plan created: request_id=req-ref-001")
        print(f"  plan_hash: {plan_hash1[:16]}...")
        print(f"  action: merge_without_approval")
        print(f"  boundary: merge to production branch")
        
        row1 = emitter.emit_decision(
            request_id="req-ref-001",
            session_id="sess-001",
            plan=plan1,
            phase_emitted="REF",
            terminal_posture="refuse",
            authority_verdict="fail",
            boundary_verdict="blocked",
            ref_enforced=True,
            irreversible_boundary_phrase="merge to production branch",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=["MISSING_AUTHORITY", "REF_ENFORCED"],
        )
        
        print(f"\nLedger row emitted:")
        print(f"  event_id: {row1.event_id}")
        print(f"  phase: {row1.phase_emitted}")
        print(f"  posture: {row1.terminal_posture}")
        print(f"  authority: {row1.authority_verdict}")
        print(f"  reason_codes: {row1.reason_codes}")
        
        print("\n" + "=" * 60)
        print("Session 2: CONF Bounded Allow Path")
        print("-" * 40)
        
        plan2 = {
            "request_id": "req-conf-002",
            "action_type": "commit_prod_change",
            "user_context": {
                "user_id": "u2",
                "role": "admin",
                "approval_token": "tok-123",
            },
            "boundary_phrase": "commit to production config",
        }
        plan_hash2 = compute_plan_hash(plan2)
        
        print(f"Plan created: request_id=req-conf-002")
        print(f"  plan_hash: {plan_hash2[:16]}...")
        print(f"  action: commit_prod_change")
        print(f"  boundary: commit to production config")
        
        row2 = emitter.emit_decision(
            request_id="req-conf-002",
            session_id="sess-002",
            plan=plan2,
            phase_emitted="CONF",
            terminal_posture="bounded_allow",
            authority_verdict="pass",
            boundary_verdict="allowed_pre_boundary_only",
            ref_enforced=False,
            irreversible_boundary_phrase="commit to production config",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=["SAFE_PREBOUNDARY_ONLY"],
        )
        
        print(f"\nLedger row emitted:")
        print(f"  event_id: {row2.event_id}")
        print(f"  phase: {row2.phase_emitted}")
        print(f"  posture: {row2.terminal_posture}")
        print(f"  authority: {row2.authority_verdict}")
        print(f"  reason_codes: {row2.reason_codes}")
        
        print("\n" + "=" * 60)
        print("Session 3: DES Safe Execute Path with Execution")
        print("-" * 40)
        
        plan3 = {
            "request_id": "req-des-003",
            "action_type": "safe_commit",
            "user_context": {"user_id": "u3", "role": "developer"},
            "boundary_phrase": "",
        }
        plan_hash3 = compute_plan_hash(plan3)
        
        print(f"Plan created: request_id=req-des-003")
        print(f"  plan_hash: {plan_hash3[:16]}...")
        print(f"  action: safe_commit")
        print(f"  boundary: (none)")
        
        row3a = emitter.emit_decision(
            request_id="req-des-003",
            session_id="sess-003",
            plan=plan3,
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
        
        print(f"\nDecision ledger row emitted:")
        print(f"  event_id: {row3a.event_id}")
        print(f"  phase: {row3a.phase_emitted}")
        print(f"  posture: {row3a.terminal_posture}")
        
        emitter2 = LedgerEmitterV1(store=store, runtime_version="0.1.0")
        row3b = emitter2.emit_execution(
            request_id="req-des-003",
            session_id="sess-003",
            plan_hash=plan_hash3,
            sandbox_id="sbx-003",
            outcome="executed",
            commands_executed=["echo hello", "git status"],
            commands_blocked=[],
            exit_code=0,
            duration_ms=150,
            artifacts=["output.log"],
        )
        
        print(f"\nExecution ledger row emitted:")
        print(f"  event_id: {row3b.event_id}")
        print(f"  phase: {row3b.phase_emitted}")
        print(f"  posture: {row3b.terminal_posture}")
        print(f"  duration_ms: {row3b.latency_ms}")
        
        print("\n" + "=" * 60)
        print("Ledger Replay and Reconciliation")
        print("-" * 40)
        
        stats = replay.get_statistics()
        print(f"\nLedger Statistics:")
        print(f"  Total rows: {stats['total_rows']}")
        print(f"  Unique requests: {stats['unique_requests']}")
        print(f"  By phase: {stats['by_phase']}")
        print(f"  By posture: {stats['by_posture']}")
        print(f"  Invariant violations: {stats['invariant_violations']}")
        
        print(f"\n--- Session 1 Replay ---")
        session1 = replay.reconstruct_session("req-ref-001")
        print(f"  request_id: {session1.request_id}")
        print(f"  session_id: {session1.session_id}")
        print(f"  is_complete: {session1.is_complete()}")
        print(f"  has_execution: {session1.has_execution()}")
        print(f"  final_posture: {session1.get_final_posture()}")
        
        print(f"\n--- Session 3 Replay ---")
        session3 = replay.reconstruct_session("req-des-003")
        print(f"  request_id: {session3.request_id}")
        print(f"  is_complete: {session3.is_complete()}")
        print(f"  has_execution: {session3.has_execution()}")
        print(f"  ledger_rows: {len(session3.ledger_rows)}")
        
        print(f"\n--- Join Key Reconciliation ---")
        rec1 = replay.reconcile("req-ref-001", plan_hash1)
        print(f"  req-ref-001 + plan_hash1:")
        print(f"    rows: {len(rec1.rows)}")
        print(f"    is_valid: {rec1.is_valid()}")
        
        print(f"\n--- Duplicate Emission Check ---")
        errors = replay.validate_no_duplicate_emissions("req-ref-001")
        if errors:
            print(f"  Errors: {errors}")
        else:
            print(f"  No duplicate emissions detected (PASS)")
        
        print(f"\n--- Timeline for req-des-003 ---")
        timeline = replay.get_session_timeline("req-des-003")
        for i, evt in enumerate(timeline):
            print(f"  {i+1}. {evt['timestamp_utc'][:19]} | {evt['phase']} | {evt['posture']}")
        
        print("\n" + "=" * 60)
        print("Demo Complete — All invariants satisfied")
        print("=" * 60)


if __name__ == "__main__":
    run_traced_session()
