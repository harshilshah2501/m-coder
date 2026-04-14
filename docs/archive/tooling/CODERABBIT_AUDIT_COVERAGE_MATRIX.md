## CodeRabbit Audit Coverage Matrix

**Human review (no CodeRabbit):** Execution playbook: [docs/audit/HUMAN_WHOLE_REPO_REVIEW.md](audit/HUMAN_WHOLE_REPO_REVIEW.md) — same sequencing as the Cursor whole-repo plan; batches A–I. **Repo layout inventory:** [docs/audit/REPO_LAYOUT_INVENTORY.md](audit/REPO_LAYOUT_INVENTORY.md). **Test coverage matrix:** [docs/audit/TEST_COVERAGE_MATRIX.md](audit/TEST_COVERAGE_MATRIX.md).

This is the live tracker for the current audit cycle.

Status values: not_started, in_review, reviewed, deferred, excluded.

## 1) Top-Level Directory Coverage

| Path | Category | Objective (A/C/R) | Status | PR Ref | Reshuffle Candidate | Notes |
|---|---|---|---|---|---|---|
| .github/ | Support | A,C | not_started |  | no | CI/workflow hardening first |
| packaging/ | Support | A,C | not_started |  | no | Reproducibility and install paths |
| runtime/ | Core | A,C,R | in_review |  | yes | Batch A governed core: [BATCH_A_GOVERNED_RUNTIME_CORE.md](audit/BATCH_A_GOVERNED_RUNTIME_CORE.md); further batches ongoing |
| jetbrains-plugin/ | Core | A,C | not_started |  | maybe | IDE integration contracts |
| ml/ | Core | A,C,R | not_started |  | maybe | Reproducibility and lineage |
| tests/ | Support | A,C | not_started |  | no | Regression proof |
| validation/ | Support | A,C | not_started |  | no | Gate clarity and determinism |
| scripts/ | Support | A,C,R | not_started |  | maybe | Operator automation safety |
| docs/ | Support | A,C,R | not_started |  | yes | Canonicalization and drift cleanup |
| governance/ | Locked | C | not_started |  | no | Consistency audit only |
| observation/ | Experimental | A,C | not_started |  | maybe | Telemetry and drift robustness |
| archive/workspace_intelligence/ | Archived spike | A,C | not_started |  | maybe | Ownership and privacy assumptions |
| archive/hostB_proof_pack/ | Archive | C | deferred |  | no | Moved from root 2026-04-13; historical payloads |
| archive/ | Archive | C | not_started |  | maybe | Exclude or reorganize policy |
| OKR/ | Support | C,R | not_started |  | maybe | Planning artifact disposition |

## 2) Second-Level Module Coverage

| Parent | Module Path | Category | Objective (A/C/R) | Status | PR Ref | Reshuffle Candidate | Notes |
|---|---|---|---|---|---|---|---|
| runtime/ | runtime/plangate/ | Core | A,C | in_review |  | no | Batch A; see [BATCH_A_GOVERNED_RUNTIME_CORE.md](audit/BATCH_A_GOVERNED_RUNTIME_CORE.md) |
| runtime/ | runtime/policies/ | Core | A,C | not_started |  | no | Authority and boundary policy |
| runtime/ | runtime/ledger/ | Core | A,C | in_review |  | no | Batch A (A-1 orchestrator ↔ store); see audit doc |
| runtime/ | runtime/orchestrator/ | Core | A,C | in_review |  | maybe | Batch A (finding A-1); see audit doc |
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
| Audit-Batch-A | Human review (governed runtime core) | plangate, orchestrator, loop, state, sandbox, execute_service, ledger | P1 ledger persist / Stage 3 gate input; see doc | n/a | [BATCH_A_GOVERNED_RUNTIME_CORE.md](audit/BATCH_A_GOVERNED_RUNTIME_CORE.md) |

## 5) Stage Exit Checklist

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
