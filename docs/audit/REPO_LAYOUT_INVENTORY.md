# REPO_LAYOUT_INVENTORY — Phase 0/1

**Status:** living document (refresh on major refactors)  
**Last updated:** 2026-04-13  
**Plan:** `~/.cursor/plans/multi-phase_layout_and_test_review_7bd5a487.plan.md` (Cursor plans; copy into repo if desired)

## How to read this doc

- **canonicality:** `canonical` | `compatibility` | `residual` | `closed-but-follow-on` | `experimental` | `archive` | `non-product`
- **in_product_slice:** `yes` | `partial` | `no` — governed IDE vertical slice vs parallel/out-of-slice work
- **closed_do_not_reopen:** `yes` = milestone/Action closed per tracker; only re-audit with **artifact-backed** regression
- **validation_artifact:** representative path or `none`
- **host_topology:** `windows_plugin` | `wsl_workspace` | `linux_native` | `gpu_runtime` | `local_only` | `tunnel_dependent` | `localhost_assumed` | `n/a` (multi: comma-separated)

**Excluded from counts (inventory hygiene):** `.git/`, `.venv/`, `**/__pycache__/**`, `.pytest_cache/`, `.dvc/cache`, `**/node_modules/**`, `jetbrains-plugin/.gradle/**`, `**/build/**` (except where noted), `runtime/.run/`, `ml/training/_build/`, `ml/training/generated/`, `packaging/**/.venv*/`, large artifact trees under `docs/validation/artifacts/**` (counted as parent bucket only).

**File counts** are approximate (`find … -type f`); use for **size class** only.

---

## 1. Top-level directories and root files

| path | purpose (one line) | ~files | size class | canonicality | in_product_slice | current_status (tracker-aligned) | closed_do_not_reopen | validation_artifact (example) | runbook_or_proof | host_topology | owner_decision |
|------|---------------------|--------|------------|--------------|------------------|----------------------------------|----------------------|-------------------------------|------------------|---------------|----------------|
| [`runtime/`](../../runtime/) | Core Python runtime: plangate, orchestrator, Ask, L5, sandbox, execute | ~869 | huge | canonical | yes | M3/M4/L5 waves closed; Action 14 PASS | yes | `docs/validation/artifacts/action14_final_acceptance/` | `docs/MOTADATA_DEMO_SETUP_RUNBOOK.md` | wsl_workspace, linux_native, gpu_runtime, localhost_assumed | TBD |
| [`docs/`](..) | Narrative specs, runbooks, validation indexes, audits | ~633 | huge | canonical | partial | Canonical tracker + closure docs | partial | `docs/validation/` tree | many under `docs/guides/`, `docs/demo/` | n/a | TBD |
| [`ml/`](../../ml/) | Training, eval, datasets, lineage (Layer-2) | ~2990 | huge | canonical | partial | L2 compilation locked; training not on hot IDE path | yes (for release ML bar) | `ml/lineage/`, `docs/COMPILATION/` | `docs/training/` | gpu_runtime, local_only | TBD |
| [`packaging/`](../../packaging/) | Installable wheels (Context Layer etc.) | ~5† / ~4200‡ | tiny src / huge with venvs | canonical | yes | L5 packaging slice complete (wheel + no checkout on WSL) | yes | `packaging/motadata-context-layer/` + validation refs | `docs/guides/` integration guides | wsl_workspace, linux_native | †source only ‡includes `motadata-context-layer/.venv*` etc. |
| [`jetbrains-plugin/`](../../jetbrains-plugin/) | Thin IDE client (Kotlin) | ~55† | medium | canonical | yes | Action 4 closed; Phase-1 truth proof LOCKED; B3 residual items optional | yes‡ | `docs/validation/artifacts/plugin_phase1_truth_proof/` | `docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md` | windows_plugin, localhost_assumed | ‡B3 checklist residual |
| [`governance/`](../../governance/) | Doctrine, policies, golden exemplars | ~266 | medium | canonical | yes | Layer-1 LOCKED | yes | governance + runtime enforcement cross-checks | `AGENT_EXECUTION_RULES.md` | n/a | TBD |
| [`archive/`](../../archive/) | Historical snapshots | ~143 | medium | archive | no | Historical reference | yes (do not “fix” forward) | none | none | n/a | archive |
| [`observation/`](../../observation/) (root) | Trace ingest, baselines (repo root) | ~128 | medium | canonical | partial | B4 closed; ops follow-through | yes | `docs/validation/` + observation tests | `docs/OBSERVATION/` | linux_native, localhost_assumed | TBD |
| [`validation/`](../../validation/) | Runtime validation harnesses, runs | ~67 | small | canonical | yes | Host proofs, stage traces | partial | `validation/runs/`, `stage2_trace_samples/` | closure docs | wsl_workspace, linux_native | TBD |
| [`archive/hostB_proof_pack/`](../../archive/hostB_proof_pack/) | Archived Host-B proof payloads (moved from repo root) | ~26 | small | archive | no | Superseded location; not on hot path | yes | per-folder README | `docs/guides/HOST_*` | varies | archived 2026-04-13 |
| [`scripts/`](../../scripts/) | CI and operator scripts | ~36 | small | canonical | yes | CI guards, one-shots | partial | `scripts/ci/` | runbooks | linux_native | TBD |
| [`tests/`](../../tests/) | Top-level pytest (subset; most tests under `runtime/tests/`) | ~3 | tiny | canonical | yes | Cross-runtime tests | partial | `tests/` + `runtime/tests/` | n/a | n/a | TBD |
| [`archive/workspace_intelligence/`](../../archive/workspace_intelligence/) | Archived L5 spike (A1); prod = `runtime/layer5/` | ~9 | tiny | archived | no | Not production slice | no | `spikes/README.md` | none | archived 2026-04-14 | — |
| [`OKR/`](../../OKR/) | Planning artifacts | ~16 | tiny | non-product | no | External to product | yes | none | none | n/a | OKR owner |
| [`motadata_context_layer.egg-info/`](../../motadata_context_layer.egg-info/) | setuptools metadata | ~5 | tiny | non-product | no | Generated | yes | none | none | n/a | exclude from review |
| [`.github/`](../../.github/) | CI workflows | ~1+ | tiny | canonical | yes | Ship gates | partial | workflow logs | CI docs | linux_native | TBD |

† JetBrains count excludes `.gradle`/`build` for signal.

### Root files (selected)

| path | purpose | canonicality | in_product_slice | notes |
|------|---------|--------------|------------------|-------|
| [`README.md`](../../README.md) | Repo entry | canonical | yes | |
| [`Makefile`](../../Makefile) | Build shortcuts | canonical | partial | |
| [`AGENT_EXECUTION_RULES.md`](../../AGENT_EXECUTION_RULES.md) | Agent doctrine | canonical | yes | |
| [`MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md`](../../MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md) | Master spec | canonical | yes | |
| [`Hardware-Profile.md`](../../Hardware-Profile.md) | Host profile notes | canonical | partial | B5/B7 context |
| [`cuda-pytorch_test.py`](../../cuda-pytorch_test.py) | GPU smoke | compatibility | partial | dev utility |
| [`.coderabbit.yaml`](../../.coderabbit.yaml) | Review bot config | non-product | no | optional tool |
| [`git_diff.txt`](../../git_diff.txt) | Local diff capture | non-product | no | consider gitignore |

---

## 2. `runtime/` — second level (~869 files)

| path | ~files | size | canonicality | in_product_slice | role | closed_do_not_reopen | validation_artifact | host_topology |
|------|--------|------|--------------|------------------|------|----------------------|---------------------|---------------|
| `runtime/layer5/` | ~243 | huge | canonical | yes | L5 evidence, ranking, harness | yes (L5.8 etc.) | `docs/validation/artifacts/` L5 | localhost_assumed |
| `runtime/tests/` | ~131 | huge | canonical | yes | Primary pytest tree | partial | `runtime/tests/` | n/a |
| `archive/legacy_runtime_rag/` | ~57 | medium | partial | partial | RAG/orchestrator; not whole IDE path | B1 closed | B1 refs in tracker | wsl_workspace |
| `runtime/plan_gate_stub/` | ~40 | medium | compatibility | no | Protocol/CLI emulator; **not** M3.3 gate | yes | stub tests | n/a |
| `runtime/observation/` | ~38 | medium | canonical | yes | Runtime observation helpers | B4 closed | trace docs | localhost_assumed |
| `runtime/schemas/` | ~27 | small | canonical | yes | JSON contracts | partial | schema validation tests | n/a |
| `runtime/shadow/` | ~25 | small | compatibility | partial | Shadow mode | partial | shadow tests | n/a |
| `runtime/ide/` | ~25 | small | canonical | yes | IDE protocol schemas | partial | | n/a |
| `runtime/assist_layer/` | ~25 | small | canonical | partial | Stage 2.5 advisory; Actions 15–17 eval | yes (advisory-only) | `docs/validation/artifacts/assist_layer_v2_eval/` | n/a |
| `runtime/sandbox/` | ~23 | medium | canonical | yes | Execution sandbox | yes | Action 14 / execute honesty | wsl_workspace, linux_native |
| `runtime/plan_gate_service/` | ~19 | small | compatibility | no | HTTP v0.1 Plan-Gate **service**; CI; not `plangate` | partial | `runtime/ci_gate/` | localhost_assumed |
| `runtime/plangate/` | ~18 | small | **canonical** | yes | **M3.3 execution gate** | yes | plangate integration tests | n/a |
| `runtime/context_layer_service/` | ~16 | small | **canonical** | yes | Export + health HTTP | yes | B5, packaging validation | wsl_workspace, linux_native |
| `runtime/context/` | ~14 | small | canonical | yes | Context engine | partial | | wsl_workspace |
| `runtime/orchestrator/` | ~12 | small | **canonical** | yes | LoopController + matrix | yes | `test_plangate_integration` | n/a |
| `runtime/ledger/` | ~12 | small | canonical | yes | Ledger semantics | partial | | n/a |
| `runtime/ask_service/` | ~12 | small | **canonical** | yes | `/v1/ask`, `/v0/ask` | yes | Ask v1 tests | localhost_assumed |
| `runtime/state/` | ~17 | small | canonical | yes | Task state | partial | stage3 tests | n/a |
| `runtime/loop/` | ~8 | tiny | **canonical** | yes | **Stage3LoopController** (distinct from orchestrator) | partial | `test_stage3_loop.py` | n/a |
| `runtime/integrity/` | ~8 | tiny | canonical | yes | M4.1 intent + guard | yes | M41 tests | n/a |
| `runtime/execute_service/` | ~4 | tiny | **canonical** | yes | `POST` execute path | yes | `test_execute_service.py` | n/a |
| `runtime/policies/` | ~6 | tiny | canonical | yes | Policy hooks | partial | | n/a |
| `runtime/ci_gate/` | ~6 | tiny | compatibility | no | CI client → plan_gate_service | partial | | n/a |
| `runtime/tools/` | ~4 | tiny | canonical | yes | Stage 3 ToolExecutor | partial | | n/a |
| `runtime/obs/` | ~4 | tiny | canonical | yes | Stage 3 ledger | partial | | n/a |
| `runtime/emulator/` | ~8 | tiny | experimental | partial | Emulator | no | | n/a |
| `runtime/replay/` | ~4 | tiny | experimental | partial | Replay | no | | n/a |
| `runtime/adapters/` | ~4 | tiny | canonical | partial | Model adapter | partial | | gpu_runtime |

**Naming note:** `runtime/orchestrator/loop_controller.py` (matrix transitions + `validated_to_sandbox`) vs `runtime/loop/loop_controller.py` (Stage 3 state machine) — **different subsystems**; do not merge mentally.

---

## 3. `docs/` — bucket level (~633 files under `docs/`)

| bucket | ~files | canonicality | in_product_slice | notes |
|--------|--------|--------------|------------------|-------|
| `docs/validation/` | ~361 | canonical | yes | Largest; artifacts + closure evidence |
| `docs/runtime/` | ~69 | canonical | yes | Runtime specs and demos |
| `docs/audit/` | ~37 | canonical | partial | Audit reports + **this inventory** |
| `docs/guides/` | ~23 | canonical | yes | Integration, temp guides |
| `docs/mvp_declaration/` | ~4 | canonical | yes | Closure authority |
| `docs/demo/` | ~7 | canonical | partial | Operator demos |
| `docs/architecture/` | ~9 | partial | yes | Architecture narratives |
| `docs/agents/` | ~1 | experimental | no | Legacy/exploratory |
| `docs/datasets/` | ~12 | partial | partial | Dataset docs |

---

## 4. `ml/` — second level (~2990 files)

| path | ~files | canonicality | in_product_slice | notes |
|------|--------|--------------|------------------|-------|
| `ml/training/` | ~2780 | partial | no | Heavy; not IDE request path |
| `ml/evaluation/` | ~82 | canonical | partial | KPI / regression |
| `ml/datasets/` | ~70 | partial | partial | |
| `ml/artifacts/` | ~34 | partial | partial | |
| `ml/lineage/` | ~22 | canonical | partial | Pins / reproducibility |
| `ml/scripts/` | ~1 | partial | no | |

---

## 5. `packaging/` — second level

| path | canonicality | in_product_slice | notes |
|------|--------------|------------------|-------|
| `packaging/motadata-context-layer/` | **canonical** | yes | Wheel + HTTP API; WSL-friendly install |

Nested `.venv*` / `dist` / `build` under packaging: **exclude** from manual review; treat as **build output**.

---

## 6. `jetbrains-plugin/` — second level

| path | canonicality | in_product_slice | host_topology |
|------|--------------|------------------|---------------|
| `jetbrains-plugin/motadata-jetbrains-plugin/` | canonical | yes | windows_plugin |
| `gradle/`, wrapper | compatibility | yes | CI |

---

## 7. `.github/`

Covered in **§1** top-level table (CI workflows).

---

## 8. Next steps (Phase 2–4)

1. **`TEST_COVERAGE_MATRIX.md`** — [done (draft)](TEST_COVERAGE_MATRIX.md): tests + validation artifacts + closure gates per package.
2. **`WORKFLOW_SCENARIO_MATRIX.md`** — closure-gate scenarios from tracker §1.3 + §3a.
3. **`SYNTHESIS_REPORT.md`** — five buckets (canonical / compatibility / needs validation / archive / future).

---

## References

- [`docs/LIVE_ROADMAP_TRACKER.md`](../LIVE_ROADMAP_TRACKER.md)
- [`docs/audit/HUMAN_WHOLE_REPO_REVIEW.md`](HUMAN_WHOLE_REPO_REVIEW.md)
- [`docs/audit/BATCH_A_GOVERNED_RUNTIME_CORE.md`](BATCH_A_GOVERNED_RUNTIME_CORE.md)
