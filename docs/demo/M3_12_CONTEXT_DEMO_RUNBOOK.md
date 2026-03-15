# M3.12 Context Demo Runbook

**Purpose:** Run a deterministic, repo-aware ask demo on the M3.12 narrow context engine. Demonstrates documentation/context selection only; PLAN_ONLY and non-executing.

**Scope:** Demo orchestration for the already-validated M3.12 slice. Not M3.13, not retrieval platform work, not plugin redesign.

---

## 1. Demo purpose

- Show that the same ask query, against the same repo revision, yields the same selected context bundle.
- Show that repo-aware selection uses path_match, heading_match, symbol, and adjacency (no embeddings or vector DB).
- Show that the ask path remains PLAN_ONLY and never executes.
- Provide a repeatable, evidence-based pass/fail for demo success.

---

## 2. Exact branch

- **Branch:** `integration/m3.12-context-demo`
- **Verification reference:** `docs/reports/M3_12_INTEGRATION_VERIFICATION_REPORT.md`

Ensure you are on this branch before running the demo:

```bash
git checkout integration/m3.12-context-demo
```

---

## 3. Demo prerequisites

| Requirement | Check |
|-------------|--------|
| Python 3.9+ | `python3 --version` |
| Repo root | Current working directory is the repository root (contains `runtime/`, `docs/`) |
| No schema/plugin changes | Ask contract is `plan_only_response.v0.1`; no execution from ask path |

Optional for full E2E: Plan-Gate service running and plugin pointed at it (not required for runbook validation).

---

## 4. Scenario list (deterministic ask scenarios)

All three scenarios are PLAN_ONLY and non-executing. Each demonstrates repo-aware documentation/context selection.

| # | Scenario | Query | What it demonstrates |
|---|----------|--------|------------------------|
| 1 | Context selection | "How does context selection work?" | Path/heading match on "context", "selection"; selects from `docs/` and/or `runtime/context/` |
| 2 | Repository context engine | "Where is the repository context engine documented?" | Path/heading match on "repository", "context", "engine"; selects docs and context modules |
| 3 | Plan-Gate | "How does Plan-Gate work?" | Path/heading match on "plan", "gate"; selects docs under ingestion allowlist |

Ingestion allowlist (default): `docs/**/*.md`, `docs/runtime/**`, `runtime/context/*.py`, `README.md`. Same repo + same query → same bundle.

---

## 5. Request examples

Use `ask_request.v0.1` shape. `repo_root` must be the repository root path.

**Scenario 1 — Context selection**

```json
{
  "schema_version": "ask_request.v0.1",
  "request_id": "demo-scenario-1",
  "timestamp_utc": "2026-03-15T12:00:00Z",
  "repo_root": "<REPO_ROOT_PATH>",
  "revision": "HEAD",
  "query": "How does context selection work?"
}
```

**Scenario 2 — Repository context engine**

```json
{
  "schema_version": "ask_request.v0.1",
  "request_id": "demo-scenario-2",
  "timestamp_utc": "2026-03-15T12:00:00Z",
  "repo_root": "<REPO_ROOT_PATH>",
  "revision": "HEAD",
  "query": "Where is the repository context engine documented?"
}
```

**Scenario 3 — Plan-Gate**

```json
{
  "schema_version": "ask_request.v0.1",
  "request_id": "demo-scenario-3",
  "timestamp_utc": "2026-03-15T12:00:00Z",
  "repo_root": "<REPO_ROOT_PATH>",
  "revision": "HEAD",
  "query": "How does Plan-Gate work?"
}
```

Replace `<REPO_ROOT_PATH>` with the absolute path to the repository root (e.g. output of `pwd` when at repo root).

---

## 6. Expected response characteristics

For every scenario:

| Field | Expected |
|-------|----------|
| `schema_version` | `"plan_only_response.v0.1"` |
| `governance_posture` | `"PLAN_ONLY"` |
| `execution` | `false` |
| `context_bundle.revision` | Present (e.g. `"HEAD"`) |
| `context_bundle.files` | Array; each element has `path` and `selection_reason` |
| `plan_summary.steps` | Array of strings (3–6 steps) |
| `plan_summary.notes` | Optional; when repo-aware selection ran, may include "Repo-aware selection: N file(s) by ..." |

Determinism: Running the same scenario twice with the same repo_root and revision must yield the same `context_bundle.files` (same paths and selection_reason values).

---

## 7. Deterministic pass/fail criteria

**Demo succeeds if and only if:**

1. **Contract:** Every response has `schema_version == "plan_only_response.v0.1"`, `governance_posture == "PLAN_ONLY"`, `execution === false`.
2. **Shape:** Every response has `context_bundle.files` (array), `plan_summary.steps` (array, length 1–10), and each file has `path` and `selection_reason`.
3. **Determinism:** For each scenario, two consecutive calls with the same `repo_root` and `revision` return identical `context_bundle.files` (same paths in same order, same selection_reason per path).
4. **Repo-aware:** For at least one scenario, `context_bundle.files` is non-empty and selection_reason includes at least one of: `path_match`, `heading_match`, `symbol:hint:...`, `adjacent:dir` (or selector `manifest` in provenance if exposed).

**Evidence that the demo succeeded:** All four criteria above hold; test run or operator checklist confirms it.

---

## 8. Known non-goals

- No execution from ask path.
- No embeddings, vector DB, or semantic retrieval expansion.
- No M3.13 Jira or M3.14 PR ingestion.
- No plugin UX redesign or ask schema change.
- No guarantee of which specific files are selected (depends on repo contents and query tokens); only that the response is valid, deterministic, and PLAN_ONLY.

---

## 9. Operator walkthrough

1. **Check branch:** `git branch --show-current` → expect `integration/m3.12-context-demo`.
2. **Set repo root:** `export REPO_ROOT=$(pwd)` (from repository root).
3. **Run validation test (if available):**  
   `python3 -m pytest runtime/tests/test_m312_demo_scenarios.py -v`  
   This runs the three scenarios against the repo and asserts pass criteria.
4. **Or run manually:** From repo root, invoke the ask handler with each request (e.g. via Plan-Gate service `/v0/ask` or by calling `handle_ask_request` in Python with `repo_root=REPO_ROOT`). For each response, verify: schema_version, governance_posture, execution, context_bundle.files shape, and run the same request again to confirm identical files list.
5. **Pass:** If all criteria in §7 hold, the demo is **M3.12 DEMO READY**.

---

*End of M3.12 Context Demo Runbook.*
