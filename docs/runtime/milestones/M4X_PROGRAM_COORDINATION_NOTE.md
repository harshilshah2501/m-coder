# M4.x Program Coordination Note

**Coordinator Branch:** `integration/m4x-program`  
**Audit Date:** 2026-03-13  
**Baseline:** M3.11 complete on main; M4.x branches diverged from `465a586`

---

## 1. Executive Summary

This note documents the repository reality for M4.1–M4.6 milestones, reconciles tracker state vs actual implementation, defines merge order, and establishes readiness criteria.

**Key Finding:** All six M4.x feature branches (`feature/m4.1-observability-closure` through `feature/m4.6-runtime-metrics`) are currently at the **same commit** (`cd2e74d`), containing only M4.1 Slice 1–4 implementation. M4.2–M4.6 have **no milestone-specific implementation** yet.

---

## 2. Branch Map

| Branch | Base | HEAD | Status |
|--------|------|------|--------|
| `main` | — | `aa3a094` | Layer-3 baseline (M3.0–M3.11 complete) |
| `integration/m4x-program` | `465a586` | `cd2e74d` | M4.1 Slices 1–4 implemented |
| `feature/m4.1-observability-closure` | `465a586` | `cd2e74d` | **ACTIVE** — M4.1 Slices 1–4 |
| `feature/m4.2-drift-baseline` | `465a586` | `cd2e74d` | **NOT_STARTED** — same as M4.1 |
| `feature/m4.3-collapse-tracking` | `465a586` | `cd2e74d` | **NOT_STARTED** — same as M4.1 |
| `feature/m4.4-ledger-reconciliation` | `465a586` | `cd2e74d` | **NOT_STARTED** — same as M4.1 |
| `feature/m4.5-greg-escalation` | `465a586` | `cd2e74d` | **NOT_STARTED** — same as M4.1 |
| `feature/m4.6-runtime-metrics` | `465a586` | `cd2e74d` | **NOT_STARTED** — same as M4.1 |

**Observation:** All M4.x branches were created from the same point and have not diverged. They all contain M4.1 work only.

---

## 3. Repository Reality Status Table

| Milestone | Tracker Status | Repo Reality | Evidence Found | Missing Artifacts | Feature Branch | Merge Order |
|-----------|----------------|--------------|----------------|-------------------|----------------|-------------|
| **M4.1** Observability Closure | NOT_STARTED | **IN_PROGRESS (Slices 1–4 complete)** | `runtime/integrity/`, `runtime/plangate/pre_gate.py`, `runtime/replay/`, 56 tests passing | Slice-4 impl note; ledger ingestion service | `feature/m4.1-observability-closure` | **1** |
| **M4.2** Drift Baseline | NOT_STARTED | **NOT_STARTED** | None | Baseline distribution service, threshold config, drift detection logic | `feature/m4.2-drift-baseline` | 2 |
| **M4.3** Collapse Tracking | NOT_STARTED | **NOT_STARTED** | None | Online collapse classifier, alert mechanism, collapse taxonomy integration | `feature/m4.3-collapse-tracking` | 3 |
| **M4.4** Ledger Reconciliation | NOT_STARTED | **NOT_STARTED** | None | Reconciliation tools, pre-SFT/post-SFT/runtime ledger join | `feature/m4.4-ledger-reconciliation` | 4 |
| **M4.5** GREG Escalation | NOT_STARTED | **NOT_STARTED** | None | Evidence package generator, escalation trigger, GREG integration | `feature/m4.5-greg-escalation` | 5 |
| **M4.6** Runtime Metrics | NOT_STARTED | **NOT_STARTED** | None | Metrics service, dashboards, alert wiring | `feature/m4.6-runtime-metrics` | 6 |

---

## 4. M4.1 Observability Closure — Detailed Status

### 4.1 Implemented Slices

| Slice | Scope | Status | Evidence |
|-------|-------|--------|----------|
| **Slice 1** | CanonicalExecutionIntent + CommandNormalizer | ✅ COMPLETE | `runtime/integrity/canonical_intent.py`, `runtime/integrity/command_normalizer.py`, 23 tests |
| **Slice 2** | Live path wiring (DeterministicGuard, Plan-Gate integration) | ✅ COMPLETE | `runtime/plangate/pre_gate.py`, `runtime/integrity/plangate_bridge.py`, 17 tests |
| **Slice 3** | Ledger identity propagation | ✅ COMPLETE | `canonical_hash` in Plan-Gate decision and sandbox execution payloads, 4 tests |
| **Slice 4** | Execution replay + canonical_hash lookup | ✅ COMPLETE | `runtime/replay/execution_replay_service.py`, `get_by_canonical_hash()`, 4 tests |

### 4.2 M4.1 Test Evidence

```
runtime/tests/test_canonical_intent.py          — 9 passed
runtime/tests/test_command_normalizer.py        — 14 passed
runtime/tests/test_deterministic_guard.py       — 12 passed
runtime/tests/test_m41_slice2_integration.py    — 13 passed
runtime/tests/test_m41_slice3_ledger_identity.py — 4 passed
runtime/tests/test_ledger_canonical_hash_lookup.py — 1 passed
runtime/tests/test_execution_replay_service.py  — 3 passed
─────────────────────────────────────────────────
Total M4.1-specific tests: 56 passed
```

### 4.3 M4.1 Remaining Work

| Item | Description | Priority |
|------|-------------|----------|
| Slice-4 impl note | Document `M4_1_SLICE4_IMPL_NOTE.md` | LOW (code complete) |
| Ledger ingestion service | Pipeline ingesting runtime ledger rows into observation storage | HIGH (blocks M4.2) |
| Shadow compatibility | Verify shadow runner uses canonical_hash when present | MEDIUM |

### 4.4 M4.1 Invariants Preserved

- ✅ No execution bypass (DeterministicGuard + Plan-Gate in path)
- ✅ Fail-closed (normalization failure → BLOCKED; guard refuse → REFUSED)
- ✅ Governance boundary (drivers unchanged; no governance in driver)
- ✅ Shadow isolation (unchanged)
- ✅ Append-only ledger (canonical_hash additive; no schema migration)
- ✅ Replay compatibility (ExecutionReplayService uses canonical_hash)

---

## 5. Dependency Graph

```
M4.1 Observability Closure
    │
    ├── Ledger ingestion service (M4.1 exit criteria)
    │
    ▼
M4.2 Drift Baseline
    │
    ├── Depends on: M4.1 ledger ingestion
    │
    ▼
M4.3 Collapse Tracking
    │
    ├── Depends on: M4.1 + M4.2 (baseline for collapse detection)
    │
    ▼
M4.4 Ledger Reconciliation
    │
    ├── Depends on: M4.1 (ledger identity)
    │
    ▼
M4.5 GREG Escalation
    │
    ├── Depends on: M4.1–M4.4 (evidence packages)
    │
    ▼
M4.6 Runtime Metrics
    │
    └── Depends on: M4.1–M4.4 (metrics sources)
```

### 5.1 Critical Path

```
M4.1 (ledger ingestion) → M4.2 (drift baseline) → M4.3 (collapse tracking)
                                                          ↓
                                              M4.5 (GREG escalation)
```

M4.4 and M4.6 can proceed in parallel after M4.1 completes.

---

## 6. Merge Order

| Order | Milestone | Prerequisite | Merge Target |
|-------|-----------|--------------|--------------|
| 1 | M4.1 | M3.11 on main | `integration/m4x-program` → `main` |
| 2 | M4.2 | M4.1 merged | `feature/m4.2-drift-baseline` → `main` |
| 3 | M4.3 | M4.2 merged | `feature/m4.3-collapse-tracking` → `main` |
| 4 | M4.4 | M4.1 merged | `feature/m4.4-ledger-reconciliation` → `main` |
| 5 | M4.5 | M4.1–M4.4 merged | `feature/m4.5-greg-escalation` → `main` |
| 6 | M4.6 | M4.1–M4.4 merged | `feature/m4.6-runtime-metrics` → `main` |

**Note:** M4.4 can merge after M4.1; M4.5 and M4.6 require M4.1–M4.4.

---

## 7. Readiness Criteria per Milestone

### M4.1 — Observability Closure

| Criterion | Status | Evidence |
|-----------|--------|----------|
| CanonicalExecutionIntent schema | ✅ | `runtime/integrity/canonical_intent.py` |
| CommandNormalizer | ✅ | `runtime/integrity/command_normalizer.py` |
| DeterministicGuard | ✅ | `runtime/plangate/pre_gate.py` |
| Ledger identity propagation | ✅ | `canonical_hash` in payloads |
| Execution replay | ✅ | `runtime/replay/execution_replay_service.py` |
| Ledger ingestion service | ❌ | NOT IMPLEMENTED |
| All M4.1 tests pass | ✅ | 56 tests passing |
| Invariants preserved | ✅ | No bypass, fail-closed, governance boundary |

**Readiness:** 90% — Ledger ingestion service required for full closure.

### M4.2 — Drift Baseline

| Criterion | Status |
|-----------|--------|
| M4.1 merged | ❌ |
| Baseline distribution service | ❌ |
| Threshold configuration | ❌ |
| Drift detection logic | ❌ |
| Tests | ❌ |

**Readiness:** 0% — Blocked on M4.1 merge.

### M4.3 — Collapse Tracking

| Criterion | Status |
|-----------|--------|
| M4.2 merged | ❌ |
| Online collapse classifier | ❌ |
| Alert mechanism | ❌ |
| Collapse taxonomy integration | ❌ |
| Tests | ❌ |

**Readiness:** 0% — Blocked on M4.2.

### M4.4 — Ledger Reconciliation

| Criterion | Status |
|-----------|--------|
| M4.1 merged | ❌ |
| Reconciliation tools | ❌ |
| Pre-SFT/post-SFT/runtime ledger join | ❌ |
| Tests | ❌ |

**Readiness:** 0% — Blocked on M4.1 merge.

### M4.5 — GREG Escalation

| Criterion | Status |
|-----------|--------|
| M4.1–M4.4 merged | ❌ |
| Evidence package generator | ❌ |
| Escalation trigger | ❌ |
| GREG integration | ❌ |
| Tests | ❌ |

**Readiness:** 0% — Blocked on M4.1–M4.4.

### M4.6 — Runtime Metrics

| Criterion | Status |
|-----------|--------|
| M4.1–M4.4 merged | ❌ |
| Metrics service | ❌ |
| Dashboards | ❌ |
| Alert wiring | ❌ |
| Tests | ❌ |

**Readiness:** 0% — Blocked on M4.1–M4.4.

---

## 8. Tracker Reconciliation Notes

### 8.1 Discrepancies

| Item | Tracker Says | Repo Reality | Resolution |
|------|--------------|--------------|------------|
| M4.1 status | NOT_STARTED | IN_PROGRESS (Slices 1–4 complete) | Update tracker to IN_PROGRESS |
| M4.1 deliverable | "Ledger Ingestion" | CanonicalExecutionIntent + DeterministicGuard + Replay | Tracker scope incomplete |
| M4.2–M4.6 branches | Implied separate work | All identical to M4.1 | Branches need divergent work |

### 8.2 Tracker Update Recommendations

1. **M4.1:** Change status from `NOT_STARTED` to `IN_PROGRESS`; add evidence for Slices 1–4.
2. **M4.1 scope:** Clarify that M4.1 includes:
   - CanonicalExecutionIntent schema and normalization
   - DeterministicGuard (pre-gate)
   - Ledger identity propagation
   - Execution replay service
   - Ledger ingestion service (remaining)
3. **M4.2–M4.6:** Confirm branches should be rebased to diverge from M4.1 once M4.1 merges.

---

## 9. Global Invariants Audit

| Invariant | Status | Evidence |
|-----------|--------|----------|
| **No execution bypass** | ✅ PRESERVED | DeterministicGuard + Plan-Gate in all paths |
| **Fail-closed behavior** | ✅ PRESERVED | Normalization failure → BLOCKED; guard refuse → REFUSED |
| **Governance boundary** | ✅ PRESERVED | Drivers unchanged; no governance in driver |
| **Shadow isolation** | ✅ PRESERVED | Shadow runner unchanged; no boundary crossing |
| **Append-only ledger** | ✅ PRESERVED | canonical_hash additive; no delete/update |
| **Replay compatibility** | ✅ PRESERVED | ExecutionReplayService uses canonical_hash |

---

## 10. Blockers

| Blocker | Impact | Resolution |
|---------|--------|------------|
| M4.1 ledger ingestion service not implemented | Blocks M4.2–M4.6 | Implement ingestion pipeline |
| M4.2–M4.6 branches have no divergent work | No milestone isolation | Rebase after M4.1 merge |
| Tracker not updated for M4.1 progress | Stale roadmap | Update LIVE_ROADMAP_TRACKER.md |

---

## 11. Recommended Actions

1. **Complete M4.1:** Implement ledger ingestion service; add Slice-4 impl note.
2. **Update tracker:** Mark M4.1 as IN_PROGRESS with evidence.
3. **Merge M4.1:** After ledger ingestion, merge `feature/m4.1-observability-closure` → `main`.
4. **Rebase M4.2–M4.6:** After M4.1 merge, rebase each branch from main.
5. **Proceed sequentially:** M4.2 → M4.3 → M4.4 → M4.5/M4.6.

---

## 12. Appendix: Test Summary

```
Full runtime test suite: 417 passed, 10 skipped
M4.1-specific tests:     56 passed

Key test files:
- runtime/tests/test_canonical_intent.py
- runtime/tests/test_command_normalizer.py
- runtime/tests/test_deterministic_guard.py
- runtime/tests/test_m41_slice2_integration.py
- runtime/tests/test_m41_slice3_ledger_identity.py
- runtime/tests/test_ledger_canonical_hash_lookup.py
- runtime/tests/test_execution_replay_service.py
```

---

*End of M4.x Program Coordination Note*
