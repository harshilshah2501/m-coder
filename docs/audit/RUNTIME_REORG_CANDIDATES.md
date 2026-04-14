# `runtime/` reorganization — candidates (phased)

**Purpose:** Record **optional** reshuffles and renames for a clearer tree **without** mandating big-bang moves. Surgical hygiene already applied is listed under **Done**.

**Principles:** Respect architecture lock; avoid churn during active branches; prefer **docs + README** over mass imports rewrites unless a gate is at risk.

---

## Done (hygiene)

| Action | Rationale |
|--------|-----------|
| **Removed `runtime/intake/`** (2026-04-14) | No `.py` sources, only `__pycache__`; no imports; not git-tracked. |
| **Removed local-only cruft** (2026-04-14) | `git_diff.txt` (scratch; already in `.gitignore`); `motadata_context_layer.egg-info/` (pip metadata; `*.egg-info/` ignored); `packaging/motadata-context-layer/` local `.venv*`, `dist/`, `build/` (regenerable; ignored). |
| **`.gitignore`** | Deduplicated duplicate `golden_exemplars` dataset line. |
| **`workspace_intelligence/` → `archive/workspace_intelligence/`** (2026-04-14) | Root spike only; prod L5 is `runtime/layer5/`. See [LAYER_ROOT_DIRECTORY_FEASIBILITY.md](../architecture/LAYER_ROOT_DIRECTORY_FEASIBILITY.md) for why big layer-prefixed renames are deferred. |

---

## Not recommended now (high churn / low payoff)

| Idea | Why defer |
|------|-----------|
| Move `runtime/tests/` → repo `tests/runtime/` | Thousands of import paths and CI paths; do only with dedicated move-only PR. |
| Merge `runtime/plan_gate_stub/` into `plan_gate_service/` | Different contracts (CLI vs HTTP); stub shared via `stub_decide` already. |
| Split `rag/src/api/rag_api.py` by module | Valid maintenance; separate refactor PR with tests. |

---

## Optional / later (evaluate per release)

### 1. Rename `runtime/obs/` → `runtime/stage3_ledger/` (or similar)

- **Problem:** `obs/` vs `observation/` is easy to confuse.
- **Cost:** Updates to `loop/`, `tests/` imports, any docs.
- **When:** After a quiet window; add **deprecation shim** `obs/__init__.py` re-exporting for one release if needed.

### 2. Rename `plan_gate_service` package (e.g. `http_plan_gate_v0_1`)

- **Problem:** Name collides mentally with `plangate.PlanGateService`.
- **Cost:** High (imports, CI, docs).
- **When:** Only if operator confusion persists; README table may be enough.

### 3. `runtime/config/` vs `runtime/.config/`

- **Current:** README mentions `.config` (exists); `runtime/config/` holds env templates — two config-related dirs.
- **Action:** Document distinction in `runtime/config/README.md` (already exists) and link from root `runtime/README.md` — **doc-only** unless merging is clearly safe.

### 4. Generated / local-only dirs

- Ensure **`runtime/.run/`** stays gitignored (runtime output).
- Do not commit **`__pycache__`** under `runtime/` (already in `.gitignore`).

---

## Decision log

| Date | Decision |
|------|----------|
| 2026-04-14 | Remove dead `runtime/intake/`; expand `runtime/README.md` with gate table + package map. |

---

## References

- [RUNTIME_DIRECTORY_AUDIT.md](RUNTIME_DIRECTORY_AUDIT.md)
- [REPO_LAYOUT_INVENTORY.md](REPO_LAYOUT_INVENTORY.md)
