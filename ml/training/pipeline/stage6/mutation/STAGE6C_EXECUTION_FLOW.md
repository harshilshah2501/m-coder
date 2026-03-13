# Stage-6C Execution Flow (Agent-Loop Harness)

Stage-6C defines a **pre-freeze execution flow** for exercising locked exemplars and variants under simulated agent loops in the ML Compilation layer.

## Structural Flow

```text
Base → Variant
↓
Apply Mutation Class
↓
Run Loop Simulation
↓
Track Collapse Vectors
↓
Ledger Entry
↓
Aggregate Metrics
↓
Pass/Fail
```

### 1. Base → Variant

* Select a LOCKED base exemplar (governance- or compilation-layer).
* Select one of its LOCKED variants (if present) inheriting the same irreversible boundary and posture.
* Identify `(exemplar_id, variant_id)` pair as the unit under test.

### 2. Apply Mutation Class

* Choose a configured **mutation_class** (e.g., paraphrase, re-grounding, pressure-intensification, relaxation, loop-drift probe).
* Apply the mutation definition to the current loop input, respecting existing variant inheritance rules (no new judgment, no boundary changes).

### 3. Run Loop Simulation

* Execute an abstract Plan → Edit → Test → Revise → Retry cycle for the chosen `(exemplar_id, variant_id)` under the active mutation_class and pressure_modifier.
* Simulate test outcomes and pressure changes; do not invoke real runtime or training systems.
* Observe whether REF / CONF / DES / MIX / CODE behavior and boundaries remain consistent across iterations.

### 4. Track Collapse Vectors

* Detect any violation of structural invariants, including Stage-6B collapse vectors and Stage-6C loop-induced classes (L1–L6).
* Classify each detected collapse into one or more taxonomy entries.
* Determine severity and structural impact with respect to dataset readiness.

### 5. Ledger Entry

* For each loop iteration, emit a **ledger record** conforming to `STAGE6C_LEDGER_SCHEMA.md`.
* Ensure that each entry captures mutation_class, pressure_modifier, dominant_phase_detected, boundary_string_match, collapse_detected, collapse_class, severity, and verdict.

### 6. Aggregate Metrics

* Aggregate ledger entries into run-level metrics as defined in `STAGE6C_METRICS_SCHEMA.md`.
* Compute total_loops_executed, iterations_per_exemplar, meaningful_mutation_attempts, meaningful_collapses, collapse_rate, collapse_class_distribution, boundary_string_identity_drift_rate, and ref_stability_rate.

### 7. Pass/Fail

* Compare aggregate metrics and collapse analysis against `STAGE6C_PASS_CRITERIA.md`.
* If **Stage-6C PASS** conditions are satisfied, the harness run is eligible to support dataset freeze decisions in the ML Compilation layer.
* If **Stage-6C FAIL** conditions are triggered, compilation must return to hardening and variant refinement before any dataset freeze is considered.

This flow runs **before dataset freeze and before SFT**, and is used solely for **structural mutation testing** of compiled judgment, not for runtime control or model training.

