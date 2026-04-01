# Stage 2 — Real Motadata AIOps checkout (WSL): testing and evaluation guide

This guide is for running the Stage 2 **retrieval + quality-gate** harness against the **full** Motadata repository on **WSL Linux**, not the bundled L5 fixture. The canonical checkout path used here is:

```text
/home/harshil/Projects/Motadata
```

**m-coder** (this repo) must be run from its own clone so `PYTHONPATH` resolves to the `runtime/` package (e.g. `/home/harshil/Harshil-PoCs/m-coder`). Retrieval **never** runs on the GPU host; it stays on WSL per product constraints.

---

## 1. What you are validating

| Layer | What runs locally |
|--------|-------------------|
| **Index + lexical retrieval** | `build_file_index` + `retrieve_lexical` on `--workspace_root` |
| **Evidence quality** | `assess_evidence_quality` (same path as L5.8 / Plan-Gate evidence semantics) |
| **Outputs** | CSV row per case, metrics report, failure log, optional `evidence_bundle.json` traces |

You are **not** validating vLLM or Plan-Gate HTTP in this runner unless you add separate E2E steps; the Stage 2 runner is **retrieval-truth** first.

---

## 2. Prerequisites

1. **WSL** with a normal Linux filesystem path to Motadata (above).
2. **Motadata** checkout present and readable (`ls /home/harshil/Projects/Motadata` succeeds).
3. **m-coder** clone with `validation/stage2_runner.py` and `validation/stage2_query_pack.json`.
4. **Python 3** available as `python3` (the runner is not invoked by `python` on all distros).

Optional but useful:

- `git` in PATH (runner records `git rev-parse HEAD` for the **m-coder** repo in the manifest).
- Enough disk/RAM for indexing a large tree (first run can take minutes).

---

## 3. One-time environment

From a WSL shell:

```bash
# m-coder repository root (adjust if your clone differs)
export M_CODER_ROOT=/home/harshil/Harshil-PoCs/m-coder

# Motadata AIOps workspace root (locked for this guide)
export MOTADATA_AIOPS_ROOT=/home/harshil/Projects/Motadata
```

Confirm:

```bash
test -d "$M_CODER_ROOT/validation" && test -d "$MOTADATA_AIOPS_ROOT" && echo OK
```

---

## 4. Exact commands — baseline run (real AIOps)

Run from **`M_CODER_ROOT`** so imports resolve.

```bash
cd "$M_CODER_ROOT"

PYTHONPATH=. python3 validation/stage2_runner.py \
  --query_pack validation/stage2_query_pack.json \
  --workspace_root "$MOTADATA_AIOPS_ROOT" \
  --output_dir validation/runs/aiops_wsl_$(date -u +%Y%m%d_%H%M%S) \
  --top_k 8 \
  --per_query_timeout_sec 120 \
  --write_traces
```

**Exit codes**

| Code | Meaning |
|------|---------|
| `0` | All **hard gates** in `stage2_metrics_report.md` passed |
| `1` | Gate failure (e.g. owner@1, false_strong_rate, no_match_precision) |
| `2` | Timeout storm (>20% cases timed out) or bad args |

**Artifacts** (under the chosen `--output_dir`):

| File | Purpose |
|------|---------|
| `stage2_results_sheet.csv` | Per-case truth: `top_1_path`, `predicted_evidence_class`, pass flags |
| `stage2_metrics_report.md` | Aggregates + thresholds + **OVERALL** |
| `stage2_failure_log.md` | Timeouts, false STRONG, empty STRONG, etc. |
| `stage2_runner_manifest.json` | `query_pack_sha256`, **`workspace_identity_hash`**, git HEAD |
| `stage2_trace_samples/trace_<case_id>/` | Optional: `evidence_bundle.json` + `case_meta.json` |

---

## 5. Regression protocol (required before trusting a “green”)

Per Stage 2 spec:

1. Run the **same** command twice with **unchanged** `stage2_query_pack.json` and **same** `MOTADATA_AIOPS_ROOT` (same commit on Motadata if you want strict repeatability).
2. Compare:
   - `workspace_identity_hash` (must match across runs for the same path).
   - `query_pack_sha256` (must match).
   - Metric values in `stage2_metrics_report.md` (should match; if not, investigate non-determinism or flaky IO).

```bash
OUT1="$M_CODER_ROOT/validation/runs/aiops_run1"
OUT2="$M_CODER_ROOT/validation/runs/aiops_run2"

cd "$M_CODER_ROOT"
PYTHONPATH=. python3 validation/stage2_runner.py \
  --query_pack validation/stage2_query_pack.json \
  --workspace_root "$MOTADATA_AIOPS_ROOT" \
  --output_dir "$OUT1" \
  --write_traces

PYTHONPATH=. python3 validation/stage2_runner.py \
  --query_pack validation/stage2_query_pack.json \
  --workspace_root "$MOTADATA_AIOPS_ROOT" \
  --output_dir "$OUT2" \
  --write_traces

jq -r '.workspace_identity_hash' "$OUT1/stage2_runner_manifest.json"
jq -r '.workspace_identity_hash' "$OUT2/stage2_runner_manifest.json"
```

---

## 6. What to evaluate (and how)

### 6.1 Hard gates (automated)

Open `stage2_metrics_report.md` in the run directory and verify **Pass** column for:

- **owner@1** ≥ 0.90  
- **owner@3** ≥ 0.95  
- **distractor_error_rate** ≤ 0.10  
- **no_match_precision** ≥ 0.95  
- **false_strong_rate** = 0  
- **action_correctness** ≥ 0.90 (when plan/action rows exist)

If **OVERALL: FAIL**, do not treat the run as Stage 2 complete.

### 6.2 Per-case inspection (CSV)

Open `stage2_results_sheet.csv` and sort/filter on:

- `overall_pass` = `false`
- `false_strong` = `true`
- `distractor_fail` = `true`
- `status` ≠ `ok`

For each failing `case_id`, read `ranked_paths` (pipe-separated) and compare to `expected_primary_owner` and `acceptable_anchors` in `validation/stage2_query_pack.json`.

### 6.3 Human audit (lightweight, required for release)

Fill `validation/stage2_human_audit_checkpoint.md` (or a copy under your run folder) using the **deterministic** three-case rule from the Stage 2 spec (STRONG spot-check, NO_MATCH/refusal spot-check, first failure or NO_MATCH fallback).

### 6.4 Traces (optional but recommended)

Under `stage2_trace_samples/trace_<id>/`:

- **`evidence_bundle.json`**: Must validate as `layer5.evidence_bundle.v1` (runner calls `validate_evidence_bundle_dict` when exporting).
- Use these to debug **grounding** without involving the model.

---

## 7. When rankings differ from the fixture pack (expected on real tree)

The checked-in `stage2_query_pack.json` is **calibrated** to `runtime/layer5/audit/fixture_noisy_aiops_workspace`. The full Motadata tree has different filenames, density, and lexical scores—**owner@1** and **anchors** will often diverge.

### 7.1 Do not “fix” production code to pass the pack

Anti-cheating rule: do not add query→answer maps. Adjust **only** the query pack (queries and expectations) or accept that gates fail until retrieval/policy improves.

### 7.2 Probe actual top-k for a case ID

Use a small one-off probe (from `M_CODER_ROOT`):

```bash
cd "$M_CODER_ROOT"
PYTHONPATH=. python3 << 'PY'
import json
from pathlib import Path
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
from runtime.layer5.retrieval.quality_gate import assess_evidence_quality
from runtime.layer5.workspace.identity import WorkspaceIdentity

ROOT = Path("/home/harshil/Projects/Motadata").resolve()
ws = str(ROOT)
wid = WorkspaceIdentity(
    canonical_root=ws,
    identity_hash=WorkspaceIdentity.compute_identity_hash(ws),
    original_input=ws,
    path_type="posix",
    is_git_repo=(ROOT / ".git").is_dir(),
)
idx = build_file_index(wid)
cfg = LexicalRetrievalConfig(include_score_diagnostics=True)

pack = json.loads(Path("validation/stage2_query_pack.json").read_text())
case = next(c for c in pack["cases"] if c["id"] == "s2.q01")  # change case id
q = case["query_text"]
r = retrieve_lexical(idx, q, top_k=8, config=cfg)
paths = [h.relative_path for h in r.hits]
print("query:", q)
for i, p in enumerate(paths, 1):
    print(i, p)
print("assess_evidence_quality:", assess_evidence_quality(q, paths).evidence_quality)
PY
```

Replace `s2.q01` with the case you are fixing.

### 7.3 What to edit in `stage2_query_pack.json`

For each case:

| Field | When to change |
|-------|----------------|
| `query_text` | Steer lexical retrieval (add class names, file basename, subsystem words) so the **correct** file ranks higher. |
| `expected_primary_owner` | Set to the **actual** primary file you accept as top-1 for this query on Motadata (POSIX path under repo root). |
| `acceptable_anchors` | List alternative correct files for **owner@3** (top-3 hit). |
| `expected_evidence_class` | Align `primary` / `allow` with `assess_evidence_quality` output for that query on this tree (use the probe script). |

Re-run the runner until gates pass or you document a **product** gap (e.g. quality gate returns STRONG for a query that should be NO_MATCH).

### 7.4 Forking the pack for AIOps (recommended)

Keep the fixture-calibrated pack intact; add a second file for WSL Motadata, e.g.:

```text
validation/stage2_query_pack.aiops_wsl.json
```

Point `--query_pack` to that file for real-tree runs. Document the SHA-256 of the pack you froze for a release in `stage2_metrics_report.md` (runner already records `query_pack_sha256` in the manifest).

---

## 8. Optional: Context Layer parity check

The runner builds evidence bundles for `--write_traces` via the same export path the IDE uses (`export_evidence_bundle_dict`). To compare **HTTP** export vs runner (same workspace, same query), start the Context Layer per your deployment, then POST `POST /v1/export_evidence` with the same `workspace_root` and `query` as a trace case. `workspace_identity_hash` in the JSON should match the manifest for the same root.

---

## 9. Troubleshooting

| Symptom | What to check |
|---------|----------------|
| `workspace_root is not a directory` | Path typo; use Linux path inside WSL, not `\\wsl$\...` from Windows. |
| Slow first run | Large repo index build; reduce scope only by **changing the workspace root** (not recommended unless you use a submodule mirror). |
| Many `TIMEOUT` | Raise `--per_query_timeout_sec`; if >20% timeout, runner exits `2` (storm guard). |
| Gates pass on fixture but fail on Motadata | Expected; follow §7. |
| `git_head_m_coder` is `unknown` | `git` not installed or not a git checkout of m-coder; harmless for metrics. |

---

## 10. Quick reference — copy/paste (your paths)

```bash
export M_CODER_ROOT=/home/harshil/Harshil-PoCs/m-coder
export MOTADATA_AIOPS_ROOT=/home/harshil/Projects/Motadata
cd "$M_CODER_ROOT"

PYTHONPATH=. python3 validation/stage2_runner.py \
  --query_pack validation/stage2_query_pack.json \
  --workspace_root "$MOTADATA_AIOPS_ROOT" \
  --output_dir validation/runs/aiops_wsl_manual \
  --write_traces
```

Evaluate: `validation/runs/aiops_wsl_manual/stage2_metrics_report.md` and CSV as in §6.

---

## 11. Related documents

- Stage 2 execution spec (runner contract, gates, trace rules): see the approved plan in `.cursor/plans/` / project planning docs.
- Observability (Plan-Gate, `trace_id`): [ACTION_5_OBSERVABILITY_CORRELATION.md](./ACTION_5_OBSERVABILITY_CORRELATION.md)
- L5.8 harness (overlapping concepts): `runtime/layer5/audit/l58_grounded_harness.py`
