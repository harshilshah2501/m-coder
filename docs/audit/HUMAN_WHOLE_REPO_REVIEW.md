# Human whole-repo review (no CodeRabbit)

This repo executes the **same review as** the Cursor plan file **`coderabbit_whole-repo_review_962d8c20.plan.md`** (typically under `~/.cursor/plans/` on your machine — the “CodeRabbit plan”) using **brutal testing + manual/static review** only. If you copy that plan into the repo for portability, link it here.

**Source of truth:** That plan file — especially **§0 Canonical execution path**, **Hard rejection rules (§2)**, **§8 sequencing**, **§9 deliverables**, **§10 triage**, **§11 false-positive watchouts**.

**Layout / closure-grade inventory (Phase 0–1):** [REPO_LAYOUT_INVENTORY.md](REPO_LAYOUT_INVENTORY.md) — canonicality, in-slice, topology, tracker-aligned status.

**Test ↔ artifact ↔ gate matrix (Phase 2):** [TEST_COVERAGE_MATRIX.md](TEST_COVERAGE_MATRIX.md) — module mapping, closure §1.3 crosswalk, gaps.

**Runtime layout audit & reorg notes:** [RUNTIME_DIRECTORY_AUDIT.md](RUNTIME_DIRECTORY_AUDIT.md), [RUNTIME_REORG_CANDIDATES.md](RUNTIME_REORG_CANDIDATES.md).  
**Not required:** CodeRabbit CLI, PR bots, or paste prompts (you *may* reuse prompt text as a reviewer checklist).

---

## How this maps to the plan

| Plan section | Human execution |
|--------------|-----------------|
| §0 | Read once per session; classify every finding as **primary / compatibility / off-path**. |
| Prompts 1,2,4 | Static review + targeted `pytest` for governance/plangate/orchestrator/execute (see batches). |
| Prompts 5,6,6b,9 | Read code paths + run loop/L5/ask/assist/sandbox tests. |
| Prompts 8,13 | Observation/ledger/trace tests + test inventory grep. |
| Prompt 7 | Kotlin/plugin review + optional `./gradlew test` where env allows. |
| Prompt 10 | Read `packaging/`, `scripts/`, `.github/`; run install/CI smoke if applicable. |
| Prompt 3 | `ml/` lineage pins, reproducibility; lower time budget. |
| Prompts 14,11 | Grep for v0/v1 routing, duplicate clients; compatibility docs vs code. |
| Prompt 12 | Canonical runbooks vs env defaults in code. |
| §9 deliverables | One markdown file per batch + rolling findings table (below). |

---

## Baseline commands (run from repo root)

Use a venv if you use one. Adjust paths if needed.

```bash
# Broad regression (catch obvious breakage early)
python3 -m pytest tests/ runtime/tests/ -q --tb=short 2>/dev/null | tail -20

# Stage 3 / loop / plangate integration (governed core)
python3 -m pytest runtime/tests/test_stage3_loop.py runtime/tests/test_plangate_integration.py \
  runtime/tests/test_execute_service.py runtime/tests/test_m41_slice2_integration.py -q --tb=short

# Optional: full runtime test tree (can be slower)
python3 -m pytest runtime/tests/ -q --tb=short
```

Record failures as **P0/P1** with test name + traceback. Green tests do not prove absence of gaps — still do **static** review for silent paths and UX honesty.

---

## Batch schedule (aligned with plan §8)

Execute **in order**. Each batch produces **`docs/audit/BATCH_*.md`** (same pattern as Batch A).

| Batch | Plan refs | Scope (paths) | Status |
|-------|-----------|---------------|--------|
| **A** | 1, 2, 4 | plangate, orchestrator, loop, state, sandbox, execute_service, ledger | [BATCH_A_GOVERNED_RUNTIME_CORE.md](BATCH_A_GOVERNED_RUNTIME_CORE.md) |
| **B** | 2 + governance | `governance/`, `runtime/policies/` + doctrine vs enforcement | not_started |
| **C** | 5, 6, 6b, 9 | layer5, ask_service, context_layer_service, assist_layer, sandbox edges | not_started |
| **D** | 8, 13 | observation, trace, ledger consumers, `tests/`, `validation/` gaps | not_started |
| **E** | 7 | `jetbrains-plugin/` truthfulness, routing | not_started |
| **F** | 10 | `packaging/`, `scripts/`, `.github/` | not_started |
| **G** | 3 | `ml/` lineage / pins (secondary) | not_started |
| **H** | 14, 11 | compatibility v1→v0, dead/duplicate paths | not_started |
| **I** | 12 | docs vs code (canonical runbooks) | not_started |

After each batch: update [CODERABBIT_AUDIT_COVERAGE_MATRIX.md](../archive/tooling/CODERABBIT_AUDIT_COVERAGE_MATRIX.md) (or rename later) with **in_review → reviewed** and PR refs when fixes merge.

---

## Rolling deliverables (plan §9)

Maintain in `docs/audit/FINDINGS_REGISTER.md` (create when first finding lands) or append to batch files:

- Prioritized table: **P0–P3**, labels, **primary/compatibility/off-path**, **confirmed vs speculative**, file evidence.
- Defer/ignore bucket for P3 and hard-rejection matches.

---

## Merge strategy

Incremental merge to `main` is fine: complete a batch → record findings → fix P0/P1 in focused PRs → merge → next batch. No dependency on CodeRabbit.

---

## When you’re “done”

- All batches **A–I** have a markdown record (or explicit **excluded** with reason).
- `FINDINGS_REGISTER` (or equivalent) has no open **P0**; **P1** either fixed or explicitly accepted with owner sign-off.
- Matrix rows moved to **reviewed** where applicable.
