# Layer-4 — Comprehensive Observation and Drift Spec

**Entry point:** [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md)

## Purpose

Layer-4 produces evidence of drift and constitutional compliance. It detects divergence from constitutional expectation and triggers GREG when thresholds are exceeded. **Layer-4 produces evidence only. It never authors doctrine.**

**Directory:** `observation/` (operator/CLI boundary). The runtime-consumed Layer-4 implementation library lives under `runtime/observation/`; both are Layer-4. Two index entrypoints: `docs/OBSERVATION/README.md` (docs-spine Layer-4 index) and `observation/README.md` (package root).

---

## Ledger Ingestion

- Consumes ingestion_batch.v0.1 (JSON or JSONL)
- Validates and reconciles by (request_id, plan_hash)
- Produces deterministic report.json, report.md
- CLI: `observation/ingest/`

---

## Baseline Metrics Store

- Captures baseline verdict distribution
- Per-phase, per-surface metrics
- Baseline mode: capture; compare mode: drift_report
- `observation/baseline/`

---

## Drift Engine

**Drift** is observed behavior that diverges from constitutional expectation: REF collapses, boundary softening, MIX-to-CONF collapse, CODE abstraction drift, phase migration in model output.

Measured via verdict distribution, collapse vectors, and ledger diff.

---

## Collapse Vector Production Classifier

Classifies observed collapses into taxonomy vectors (REF_SOFTENING, CONF_TO_DES, BOUNDARY_ALIASING, MIX_SINGLE_PRESSURE, etc.). Tracks in production via drift probes.

---

## Boundary Integrity Monitor

Detects boundary relocation, aliasing, or abstraction shifts. Flags when irreversible boundary phrase diverges from freeze manifest.

---

## Phase Dominance Monitor

Validates that emitted phase aligns with constitutional expectation. REF dominance violations flagged.

---

## Runtime Invariance Comparator

Compares runtime ledger output to freeze manifest and baseline. Detects phase migration, collapse rate drift.

---

## Anomaly Detection

Flags outliers in verdict distribution, collapse rate, or phase distribution. Threshold-based; structural definition of thresholds, not hardcoded numbers in this spec.

---

## Evidence Package Builder

Assembles admissible evidence for GREG: locked exemplars, phase semantics, ledgers, collapse classifications, boundary hashes.

---

## Cryptographic Evidence Sealing

- boundary_phrase_hash per boundary_hashing.v0.1
- plan_hash links ledger to plan
- corpus_hash, split_hashes from freeze manifest

---

## GREG Escalation Trigger

When drift exceeds thresholds: REF collapse above threshold; boundary relocation detected; MIX-to-CONF collapse above threshold; CODE erosion. Produces evidence package; triggers governance review. **Observation never authors exemplars or changes judgment.**

---

## Drift Thresholds

Structurally defined. Threshold values (numeric) are configuration, not spec. Threshold types: REF collapse rate, boundary integrity, phase dominance, collapse vector distribution.

---

## Failure Modes

- Baseline incomplete; missing phases
- Probes fail; tracking gaps
- Reconciliation fails; dashboard incomplete
- GREG automation missing; thresholds misconfigured
- Evidence insufficient for lock signal

---

## Definition of Done (Layer-4)

- Drift baseline captured
- Collapse vectors tracked in production
- Ledger reconciliation dashboard operational
- GREG-trigger automation runs on drift thresholds
- Constitutional version lock signal emitted when evidence suffices

---

## What Layer-4 Must Never Do

- Author doctrine
- Relax boundaries
- Redefine phase semantics
- Modify exemplars
- Bypass GREG for governance changes
