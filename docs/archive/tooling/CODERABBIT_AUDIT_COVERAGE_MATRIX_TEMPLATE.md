## CodeRabbit Audit Coverage Matrix Template

Purpose: ensure every directory/module/submodule is explicitly reviewed, deferred, or excluded, while keeping PRs surgical.

Use this file as a live tracker during the audit cycle.

### Status Legend
- not_started: not yet reviewed
- in_review: active PR/review in progress
- reviewed: reviewed and accepted for this cycle
- deferred: intentionally postponed with reason
- excluded: intentionally out of scope (generated, cache, archive, vendor mirror)

### Category Legend
- Core: production-critical behavior
- Support: tooling/build/test/docs support
- Experimental: non-core or exploratory
- Archive: historical, not active
- Generated: auto-generated artifacts/output
- Locked: governance/schema/invariants that are consistency-audit only

### Objective Flags
- A: alignment with system objectives
- C: consistency across docs/code/runtime
- R: reshuffle candidate

## 1) Top-Level Directory Coverage

| Path | Category | Objective (A/C/R) | Status | PR Ref | Reshuffle Candidate | Notes |
|---|---|---|---|---|---|---|
| .github/ | Support | A,C | not_started |  | no | CI/workflow hardening first |
| packaging/ | Support | A,C | not_started |  | no | Reproducibility and install paths |
| runtime/ | Core | A,C,R | not_started |  | yes | Split into micro-PRs |
| jetbrains-plugin/ | Core | A,C | not_started |  | maybe | IDE integration contracts |
| ml/ | Core | A,C,R | not_started |  | maybe | Reproducibility and lineage |
| tests/ | Support | A,C | not_started |  | no | Regression proof |
| validation/ | Support | A,C | not_started |  | no | Gate clarity and determinism |
| scripts/ | Support | A,C,R | not_started |  | maybe | Operator automation safety |
| docs/ | Support | A,C,R | not_started |  | yes | Canonicalization and drift cleanup |
| governance/ | Locked | C | not_started |  | no | Consistency audit only |
| observation/ | Experimental | A,C | not_started |  | maybe | Telemetry and drift robustness |
| archive/workspace_intelligence/ | Archived spike | A,C | not_started |  | maybe | Ownership and privacy assumptions |
| archive/hostB_proof_pack/ | Archive | C | deferred |  | no | Historical Host-B payloads (if present) |
| archive/ | Archive | C | not_started |  | maybe | Exclude or reorganize policy |
| OKR/ | Support | C,R | not_started |  | maybe | Planning artifact disposition |

## 2) Second-Level Module Coverage (seed rows)

Add one row per module/submodule you touch or classify.

| Parent | Module Path | Category | Objective (A/C/R) | Status | PR Ref | Reshuffle Candidate | Notes |
|---|---|---|---|---|---|---|---|
| runtime/ | runtime/plangate/ | Core | A,C | not_started |  | no | Gate correctness and fail-closed |
| runtime/ | runtime/policies/ | Core | A,C | not_started |  | no | Authority and boundary policy |
| runtime/ | runtime/ledger/ | Core | A,C | not_started |  | no | Append-only and hash integrity |
| runtime/ | runtime/orchestrator/ | Core | A,C | not_started |  | maybe | State and loop control |
| runtime/ | runtime/assist_layer/ | Core | A,C | not_started |  | maybe | Validation and augmentation |
| runtime/ | runtime/context_layer_service/ | Core | A,C | not_started |  | maybe | Index/cache boundaries |
| runtime/ | runtime/plan_gate_service/ | Core | A,C | not_started |  | maybe | API timeout/fallback behavior |
| ml/ | ml/training/pipeline/ | Core | A,C | not_started |  | maybe | Lineage and determinism |
| ml/ | ml/evaluation/ | Core | A,C | not_started |  | no | KPI and regression checks |
| jetbrains-plugin/ | jetbrains-plugin/motadata-jetbrains-plugin/src/ | Core | A,C | not_started |  | maybe | Threading/lifecycle/API compat |
| docs/ | docs/architecture/ | Support | A,C,R | not_started |  | yes | Canonical docs pruning |
| docs/ | docs/audit/ | Support | C,R | not_started |  | yes | Likely archival/noise-heavy |
| scripts/ | scripts/ci/ | Support | A,C | not_started |  | no | CI structural guards |
| observation/ | observation/ingest/ | Experimental | A,C | not_started |  | maybe | Ingestion robustness |
| observation/ | observation/baseline/ | Experimental | A,C | not_started |  | maybe | Drift baseline stability |

## 3) Exclusion Register

Track intentionally excluded paths with reason.

| Path Pattern | Reason | Owner Decision | Date |
|---|---|---|---|
| .venv/** | Environment cache | excluded | |
| **/__pycache__/** | Python cache | excluded | |
| **/.pytest_cache/** | Test cache | excluded | |
| **/.dvc/cache/** | Data cache | excluded | |
| ml/training/_build/** | Generated build output | excluded | |
| ml/training/generated/** | Generated output | excluded | |
| archive/** | Historical content | deferred/excluded | |

## 4) PR Ledger

| PR ID | Subsystem | Scope Paths | Risk Focus | Tests Run | Outcome |
|---|---|---|---|---|---|
| PR-0 | CodeRabbit rules | .coderabbit.yaml | review noise and scope control | n/a | |

## 5) Stage Exit Checklist (run for each PR)

- [ ] Scope matches declared subsystem only
- [ ] No mixed move + logic changes
- [ ] CodeRabbit findings triaged (P0/P1/P2)
- [ ] Targeted tests passed
- [ ] One cross-subsystem smoke check passed
- [ ] Matrix rows updated with PR ref and status
- [ ] Team summary written (risk checked, change made, residual risk)

## 6) Audit Completion Criteria

- [ ] All top-level rows are reviewed/deferred/excluded
- [ ] Critical second-level modules have explicit status and PR refs
- [ ] Reshuffle decisions logged with separate move-only PR refs
- [ ] Deferred items moved to next-cycle backlog with rationale
- [ ] Final risk matrix published
