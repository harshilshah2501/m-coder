# Layer-3 Milestone Normalization Report

**Date:** 2026-03-13  
**Scope:** Documentation-only. One canonical Layer-3 numbering model applied across live roadmap docs. No code, tests, schemas, governance, or ML artifacts were modified.

---

## 1. Canonical model adopted

The repository now uses **one uniform canonical Layer-3 numbering model** in all live roadmap and progress documents:

- **M3.0** — Deterministic Runtime Emulator  
- **M3.1** — Deterministic Agent State Transition Table  
- **M3.2** — Repository Context Engine  
- **M3.3** — Agent Loop Orchestrator  
- **M3.4** — Execution Sandbox  
- **M3.5** — Plan-Gate Integration  
- **M3.6** — Internal Plan-Gate Decomposition  
- **M3.7** — IDE Plugin Integration  
- **M3.8** — Ledger Emission / Replay  
- **M3.9** — Shadow Mode Validation  
- **M3.10** — Sandbox driver abstraction  
- **M3.11** — Container sandbox runtime  
- **M3.12** — Documentation ingestion  
- **M3.13** — Jira ingestion  
- **M3.14** — PR ingestion  
- **M3.15** — Jira cleaning pipeline  
- **M3.16** — PR signal extraction  
- **M3.17** — Task schema  
- **M3.18** — Task evaluation harness  

No alternate naming (M3.E0, M3.T0, M3X.*, M3.6A/M3.6B) remains in live roadmap docs. Historical truth is preserved in git history, tags, merge commits, and completion reports; legacy labels in **historical** reports are intentionally left as-is except for a short mapping note where needed.

---

## 2. Mapping from prior naming to canonical

| Prior / mixed naming | Canonical naming |
|----------------------|------------------|
| M3.E0                | M3.0  |
| M3.T0                | M3.1  |
| M3.0 (Context Engine) | M3.2  |
| M3.1 (Orchestrator)  | M3.3  |
| M3.2 (Sandbox)       | M3.4  |
| M3.3 (Plan-Gate)     | M3.5  |
| M3.3B                | M3.6  |
| M3.4 (IDE Plugin)    | M3.7  |
| M3.5 (Ledger)        | M3.8  |
| M3.6 (Shadow)        | M3.9  |
| M3X.1                | M3.10 |
| M3X.2                | M3.11 |
| M3X.3                | M3.12 |
| M3X.4                | M3.13 |
| M3X.5                | M3.14 |
| M3X.6                | M3.15 |
| M3X.7                | M3.16 |
| M3X.8                | M3.17 |
| M3X.9                | M3.18 |

---

## 3. Status preserved (canonical IDs)

- **M3.0** — VALIDATING  
- **M3.1** — COMPLETE  
- **M3.2** — VALIDATING  
- **M3.3** — COMPLETE  
- **M3.4** — COMPLETE  
- **M3.5** — COMPLETE  
- **M3.6** — COMPLETE  
- **M3.7** — COMPLETE  
- **M3.8** — COMPLETE  
- **M3.9** — COMPLETE  
- **M3.10–M3.18** — NOT_STARTED  

Tag **layer3-runtime-governed-v1** and merge **integration/layer3-next-verification** unchanged. Evidence log (§6) labels were updated to canonical IDs; evidence bodies were not rewritten.

---

## 4. Files updated

| File | Changes |
|------|--------|
| **docs/LIVE_ROADMAP_TRACKER.md** | Single Layer-3 table M3.0–M3.18; removed Runtime v1 vs M3X split and all M3X.* / M3.E0 / M3.T0. Evidence and artifact-detail headers renamed to canonical IDs. §5 next milestones: M4.1, M3.10, M3.11. M4.1 dependency set to M3.8. |
| **docs/SYSTEM_EXECUTION_ROADMAP.md** | Layer-3 references aligned to canonical M3.0–M3.18; removed M3X.* and alternate numbering. |
| **docs/ROADMAP_L2_L3_L4.md** | Layer-3 table replaced with canonical M3.0–M3.18; snapshot and sequencing updated; M4.1 entry set to M3.9. |
| **docs/runtime/verification/LAYER3_MILESTONE_NORMALIZATION_REPORT.md** | This file; updated to describe one canonical model and mapping table. |

---

## 5. Historical reports (legacy labels)

The following may still contain **legacy** milestone labels (e.g. M3.E0, M3.1, M3.5, M3.6 in the old sense). They are **historical** evidence; content was not rewritten. For current canonical numbering, see **LIVE_ROADMAP_TRACKER.md** §4.3.1.

- **docs/runtime/verification/LAYER3_RUNTIME_COMPLETION_REPORT.md** — Describes integration that corresponds to M3.3, M3.8, M3.9 in canonical terms.  
- **docs/runtime/verification/LAYER3_PARALLEL_BRANCH_AUDIT_REPORT.md** — Branch audit; milestone IDs there may use pre-canonical naming.  
- **docs/runtime/verification/LAYER3_INTEGRATION_MERGE_READINESS_REPORT.md** — Merge readiness; same note.  

If a historical report title would cause serious confusion, a one-line note was added: *This report predates canonical Layer-3 milestone renumbering; see LIVE_ROADMAP_TRACKER.md for the current canonical numbering.*

---

## 6. Summary

- **One canonical model:** M3.0–M3.18 only in live roadmap docs.  
- **No M3X.*, no M3.6A/M3.6B,** no dual numbering.  
- **Evidence preserved:** Tag, merge, tests, demos unchanged; only labels/headers normalized to canonical IDs.  
- **Traceability:** Mapping table (§2) links prior naming to canonical for historical reports and git history.
