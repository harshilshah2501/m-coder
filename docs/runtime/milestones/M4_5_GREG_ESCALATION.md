# M4.5 GREG Governance Escalation — Milestone Note

**Status:** IN_PROGRESS  
**Branch:** feature/m4.5-greg-escalation  
**Created:** 2026-03-13  
**Last Updated:** 2026-03-13

---

## 1. Objective

Turn significant runtime drift, collapse evidence, or mismatch patterns into deterministic, governance-ready escalation bundles for GREG (Governance Review and Escalation Group) review.

**Purpose:**
- Provide structured evidence packages for governance escalation
- Enable threshold-based detection of governance-relevant anomalies
- Preserve complete ledger reference chains for audit
- Support deterministic, reproducible escalation decisions

---

## 2. Scope

### In Scope

1. **Escalation policy evaluation** — Threshold-based detection of:
   - Mismatch count breaches
   - Collapse vector accumulation
   - Drift percentage threshold breaches
   - Authority failure spikes
   - Boundary anomalies
   - Integrity violations

2. **Evidence bundle construction** — Structured bundles containing:
   - Summary statistics
   - Affected request IDs and canonical hashes
   - Mismatch/collapse/drift/integrity evidence
   - Ledger references for evidence chain
   - Classification breakdowns

3. **Bundle serialization** — Deterministic JSON serialization with:
   - Content-based bundle IDs
   - Round-trip serialization/deserialization
   - Threshold snapshots for audit

4. **Tests** — 40 tests covering:
   - Policy threshold evaluation
   - Evidence data structures
   - Bundle construction
   - Serialization round-trips
   - Integration flows

### Out of Scope

- External service calls (no webhooks, no notifications)
- Human workflow tooling
- Runtime decision modification
- Ledger ingestion pipeline (M4.1 dependency)
- Drift baseline computation (M4.2 dependency)
- Live collapse tracking (M4.3 dependency)
- Ledger reconciliation queries (M4.4 dependency)
- Dashboard or metrics visualization (M4.6)

---

## 3. Artifacts

### Implementation Files

| File | Purpose |
|------|---------|
| `runtime/observation/__init__.py` | Package exports |
| `runtime/observation/greg_escalation.py` | Escalation policy, thresholds, decisions, triggers |
| `runtime/observation/greg_bundle.py` | GREG bundle, evidence structures, ledger references |
| `runtime/observation/bundle_builder.py` | Bundle construction from raw inputs |

### Test Files

| File | Purpose |
|------|---------|
| `runtime/tests/test_greg_escalation.py` | 40 comprehensive tests |

### Documentation

| File | Purpose |
|------|---------|
| `docs/runtime/milestones/M4_5_GREG_ESCALATION.md` | This milestone note |

---

## 4. Design

### 4.1 Escalation Policy

The `EscalationPolicy` class evaluates observation inputs against configurable thresholds:

```python
policy = EscalationPolicy(thresholds=EscalationThresholds())
decision = policy.evaluate(observation_input)
# decision.should_escalate: bool
# decision.overall_severity: EscalationSeverity
# decision.triggers: list[EscalationTrigger]
```

**Escalation Types:**
- `MISMATCH_THRESHOLD` — Count-based mismatch detection
- `COLLAPSE_VECTOR` — Collapse vector accumulation
- `DRIFT_BREACH` — Percentage-based drift detection
- `AUTHORITY_FAILURE_SPIKE` — Authority failure count
- `BOUNDARY_ANOMALY` — Boundary-related anomalies
- `INTEGRITY_VIOLATION` — Always critical severity

**Severity Levels:** LOW → MEDIUM → HIGH → CRITICAL

### 4.2 Evidence Structures

Evidence is classified and structured for governance review:

- `MismatchEvidence` — Phase, posture, boundary, authority, hash, execution mismatches
- `CollapseEvidence` — REF_SOFTENING, CONF_TO_DES, BOUNDARY_RELOCATION, etc.
- `DriftEvidence` — Baseline vs observed values with drift percentage
- `IntegrityEvidence` — Hash mismatches, violation descriptions
- `LedgerReference` — Links to ledger rows for evidence chain

### 4.3 GREG Bundle

The `GREGBundle` is the final output:

```python
bundle = GREGBundle(
    bundle_id="greg-abc123...",
    created_at="2026-03-13T12:00:00Z",
    severity="high",
    summary=BundleSummary(...),
    evidence=EscalationEvidence(...),
    affected_request_ids=[...],
    affected_canonical_hashes=[...],
    thresholds_snapshot={...},
)
```

**Serialization:** Deterministic JSON with `bundle.to_json()` and `GREGBundle.from_json()`.

### 4.4 Bundle Builder

The `BundleBuilder` constructs bundles from raw inputs:

```python
builder = BundleBuilder(thresholds=thresholds, runtime_version="0.1.0")
inputs = BundleInputs(mismatches=[...], collapses=[...], ...)
bundle, decision = builder.build(inputs)
```

---

## 5. Invariants Preserved

Per AGENT_EXECUTION_RULES.md and ARCHITECTURE_FREEZE_v1.md:

| Invariant | Status |
|-----------|--------|
| No execution bypass | ✓ Preserved — no runtime modification |
| Fail-closed behavior | ✓ Preserved — no fallback paths |
| Governance boundary | ✓ Preserved — evidence only, no decisions |
| Shadow isolation | ✓ Preserved — no boundary crossing |
| Append-only ledger | ✓ Preserved — ledger references only |
| Replay compatibility | ✓ Preserved — deterministic serialization |

**Additional guarantees:**
- Deterministic: same inputs → same bundle (fixed timestamp for tests)
- No external calls: pure computation
- No runtime modification: evidence packaging only

---

## 6. Dependencies

### Upstream (Required Before Integration)

| Dependency | Milestone | Status | Notes |
|------------|-----------|--------|-------|
| Ledger emission | M3.8 | COMPLETE | Provides ledger rows for evidence |
| Canonical execution intent | M4.1 | IN_PROGRESS | Provides canonical_hash for identity |

### Lateral (Integration Points)

| Dependency | Milestone | Status | Notes |
|------------|-----------|--------|-------|
| Drift baseline | M4.2 | NOT_STARTED | Provides drift thresholds/baselines |
| Collapse tracking | M4.3 | NOT_STARTED | Provides collapse vector detection |
| Ledger reconciliation | M4.4 | NOT_STARTED | Provides reconciliation queries |

### Downstream (Consumers)

| Consumer | Milestone | Notes |
|----------|-----------|-------|
| Runtime metrics | M4.6 | May consume escalation counts |
| GREG process | L1 | Human review of bundles |

---

## 7. Test Evidence

```
$ python3 -m pytest runtime/tests/test_greg_escalation.py -v

runtime/tests/test_greg_escalation.py::TestEscalationThresholds::test_default_thresholds PASSED
runtime/tests/test_greg_escalation.py::TestEscalationThresholds::test_custom_thresholds PASSED
runtime/tests/test_greg_escalation.py::TestEscalationThresholds::test_thresholds_to_dict PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_no_triggers_no_escalation PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_mismatch_threshold_low PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_mismatch_threshold_critical PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_collapse_vector_single PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_collapse_vector_critical PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_drift_percentage_low PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_drift_percentage_critical PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_authority_failure_medium PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_boundary_anomaly_high PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_integrity_violation_always_critical PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_multiple_triggers_max_severity PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_deterministic_evaluation PASSED
runtime/tests/test_greg_escalation.py::TestEscalationPolicy::test_affected_ids_limited PASSED
runtime/tests/test_greg_escalation.py::TestEscalationDecision::test_decision_to_dict PASSED
runtime/tests/test_greg_escalation.py::TestEscalationDecision::test_evaluation_id_generated PASSED
runtime/tests/test_greg_escalation.py::TestLedgerReference::test_ledger_ref_round_trip PASSED
runtime/tests/test_greg_escalation.py::TestMismatchEvidence::test_mismatch_evidence_round_trip PASSED
runtime/tests/test_greg_escalation.py::TestCollapseEvidence::test_collapse_classifications PASSED
runtime/tests/test_greg_escalation.py::TestEscalationEvidence::test_total_count PASSED
runtime/tests/test_greg_escalation.py::TestEscalationEvidence::test_affected_request_ids_unique PASSED
runtime/tests/test_greg_escalation.py::TestGREGBundle::test_bundle_to_json PASSED
runtime/tests/test_greg_escalation.py::TestGREGBundle::test_bundle_round_trip PASSED
runtime/tests/test_greg_escalation.py::TestGREGBundle::test_content_hash_deterministic PASSED
runtime/tests/test_greg_escalation.py::TestBundleBuilder::test_empty_inputs_no_escalation PASSED
runtime/tests/test_greg_escalation.py::TestBundleBuilder::test_mismatch_inputs_produce_bundle PASSED
runtime/tests/test_greg_escalation.py::TestBundleBuilder::test_collapse_inputs_produce_bundle PASSED
runtime/tests/test_greg_escalation.py::TestBundleBuilder::test_drift_inputs_produce_bundle PASSED
runtime/tests/test_greg_escalation.py::TestBundleBuilder::test_integrity_violation_critical PASSED
runtime/tests/test_greg_escalation.py::TestBundleBuilder::test_bundle_id_deterministic PASSED
runtime/tests/test_greg_escalation.py::TestBundleBuilder::test_observation_window_preserved PASSED
runtime/tests/test_greg_escalation.py::TestBundleBuilder::test_thresholds_snapshot_included PASSED
runtime/tests/test_greg_escalation.py::TestBundleBuilder::test_build_from_decision PASSED
runtime/tests/test_greg_escalation.py::TestBundleBuilder::test_summary_classification_breakdown PASSED
runtime/tests/test_greg_escalation.py::TestBundleInputsConversion::test_to_observation_input_mismatches PASSED
runtime/tests/test_greg_escalation.py::TestBundleInputsConversion::test_to_observation_input_drift PASSED
runtime/tests/test_greg_escalation.py::TestEscalationIntegration::test_full_escalation_flow PASSED
runtime/tests/test_greg_escalation.py::TestEscalationIntegration::test_custom_thresholds_integration PASSED

============================== 40 passed ==============================
```

---

## 8. Usage Examples

### Basic Escalation Evaluation

```python
from runtime.observation import EscalationPolicy, ObservationInput

policy = EscalationPolicy()
observation = ObservationInput(
    mismatch_count=25,
    mismatch_request_ids=["req-1", "req-2", ...],
    collapse_vectors=[
        {"request_id": "req-1", "collapse_type": "REF_SOFTENING"},
    ],
)

decision = policy.evaluate(observation)
if decision.should_escalate:
    print(f"Escalation required: {decision.overall_severity.value}")
    for trigger in decision.triggers:
        print(f"  - {trigger.escalation_type.value}: {trigger.count} (threshold: {trigger.threshold_breached})")
```

### Building a GREG Bundle

```python
from runtime.observation import BundleBuilder, BundleInputs, RawMismatch, RawCollapse

builder = BundleBuilder(runtime_version="0.1.0")
inputs = BundleInputs(
    mismatches=[
        RawMismatch(
            request_id="req-1",
            canonical_hash="abc123",
            classification="phase_mismatch",
            expected_value="REF",
            actual_value="DES",
            ledger_refs_raw=[
                {"event_id": "evt-1", "event_type": "plangate_refused", ...},
            ],
        ),
        ...
    ],
    collapses=[...],
    observation_window_start="2026-03-13T00:00:00Z",
    observation_window_end="2026-03-13T12:00:00Z",
)

bundle, decision = builder.build(inputs)
print(bundle.to_json(indent=2))
```

---

## 9. Exit Criteria

| Criterion | Status |
|-----------|--------|
| Escalation policy evaluates all trigger types | ✓ |
| Bundle builder constructs valid bundles | ✓ |
| Evidence structures preserve ledger references | ✓ |
| Deterministic serialization | ✓ |
| 40 tests passing | ✓ |
| No external calls | ✓ |
| No runtime decision modification | ✓ |
| Milestone note created | ✓ |

---

## 10. Known Limitations

1. **No ledger query integration** — M4.4 required for direct ledger queries
2. **No live drift detection** — M4.2 required for baseline comparison
3. **No collapse detector integration** — M4.3 required for live collapse detection
4. **Manual input required** — Upstream milestones needed for automated detection

---

## 11. Merge Readiness

**Merge Order:** M4.5 can merge after M4.1 (canonical_hash) is merged.

**Pre-merge Checklist:**
- [x] All tests passing (40/40)
- [x] No protected files modified
- [x] Invariants preserved
- [x] Documentation complete
- [ ] M4.1 merged (dependency)

**Merge Risks:**
- None identified. Module is additive with no modifications to existing code.

---

## 12. Follow-up Work

After upstream milestones complete:

1. **M4.2 integration** — Connect to drift baseline for automatic drift detection
2. **M4.3 integration** — Connect to collapse tracker for live collapse detection
3. **M4.4 integration** — Query ledger directly for evidence construction
4. **M4.6 integration** — Expose escalation metrics to runtime metrics dashboard
