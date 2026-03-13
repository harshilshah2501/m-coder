# Repository Structure Audit

**Report date:** 2026-03-13  
**Canonical state reference:** [SYSTEM_CANONICAL_STATE_AUDIT.md](SYSTEM_CANONICAL_STATE_AUDIT.md)  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## 1. Scope

Audit top-level layout, directory casing, duplicate semantic homes, and architecture alignment. Verify Layer-1→governance/, Layer-2→ml/, Layer-3→runtime/, Layer-4→observation/. Flag mixed-case directory families, semantic duplication, and layer code outside expected top-level homes.

---

## 2. Top-Level Layout Summary

| Directory | Present | Layer / role |
|-----------|---------|--------------|
| `governance/` | Yes | Layer-1 |
| `ml/` | Yes | Layer-2 |
| `runtime/` | Yes | Layer-3 |
| `observation/` | Yes | Layer-4 |
| `docs/` | Yes | Documentation |
| `jetbrains-plugin/` | Yes | Plugin (L3 client) |
| `scripts/` | Yes | Utilities |
| `tests/` | Yes | Top-level tests |
| `archive/` | Yes | Archived content |

No `docs/GOVERNANCE` or `docs/RUNTIME` (uppercase). Only `docs/governance` and `docs/runtime` (lowercase).

---

## 3. Mixed-Case / Duplicate Directory Findings

- **docs subdirs (case-sensitive):** `docs/COMPILATION`, `docs/CONTRACTS`, `docs/OBSERVATION` exist (uppercase). `docs/governance`, `docs/runtime` exist (lowercase). No pair such as both `docs/GOVERNANCE` and `docs/governance` — no collision.
- **Semantic duplication:** Two governance-related locations: `governance/` (content) and `docs/governance/` (AGENT_EXECUTION_RULES copy + README). Documented and intentional; not flagged as error.
- **Finding:** Mixed-case under docs (COMPILATION, CONTRACTS, OBSERVATION) is recorded; root `observation/` is distinct from `docs/OBSERVATION` (different role). No conflict.

---

## 4. Layer-to-Directory Alignment

| Layer | Expected top-level | Found | Notes |
|-------|--------------------|-------|------|
| Layer-1 | governance/ | Yes | golden-exemplars, review-packages, constitutional docs |
| Layer-2 | ml/ | Yes | artifacts, datasets, evaluation, lineage, scripts, training |
| Layer-3 | runtime/ | Yes | orchestrator, plangate, sandbox, ledger, shadow, execute_service, ide, schemas, etc. |
| Layer-4 | observation/ | Yes | baseline, ingest, judge_drift_suite, tests |

Alignment holds.

---

## 5. Architecture Drift Findings

- **Ledger / SandboxLedgerStore / emit_ledger:** Grep limited to `*.py` shows matches only under `runtime/` (runtime/sandbox, runtime/tests). No ledger implementation outside runtime/.
- **train_stage08 / compile_stage7 / freeze (pipeline):** Matches under `ml/training/` (pipeline/stage08, compiler, stage6c/freeze), plus `ml/training/sft/stage7`, `ml/lineage`, `ml/training/artifacts`. Scripts and observation also reference "freeze" or similar (e.g. observation baseline metrics, scripts) — these are not Layer-2 pipeline code; they are utilities/observation. **Conclusion:** No Layer-2 pipeline code outside ml/.
- **Governance exemplar/doctrine code:** Golden exemplars and constitutional content under `governance/` and docs; no governance implementation outside governance/ or docs.

**Verdict:** No architecture drift identified. Layer code resides in expected top-level directories.

---

## 6. Pass/Fail Verdict

**PASS.** Top-level layout matches 4-layer mapping; no conflicting mixed-case pairs (GOVERNANCE/governance, RUNTIME/runtime); Layer-1→governance/, Layer-2→ml/, Layer-3→runtime/, Layer-4→observation/ verified; no layer code found outside expected homes.
