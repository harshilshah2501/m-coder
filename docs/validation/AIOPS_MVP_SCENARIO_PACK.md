# AIOps MVP Scenario Pack (WSL, Repo-Grounded)

## 1) Purpose and scope

**Operator validation:** real **Motadata** repo queries from **WSL**, using the **Context Layer → Plan-Gate** path that matches production (`layer5.evidence_bundle.v1` → **`POST /v1/ask`**).

### What this proves

- Answers are driven by **exported evidence**, not generic LLM-only text.
- Weak or ambiguous queries get **honest** handling (see rubric + D2).
- Plan-Gate responses include **deterministic retrieval-usefulness signals** (`metadata.operator_hints`, `metadata.usefulness_metrics`) so you can correlate weak/strong evidence with path mix and snippet anchoring without guessing (**§2.7**).
- This pack is **usefulness / demo validation**, not production sign-off (**§1** “does not validate”, **§8** scope guard).

### Prerequisites

| Prerequisite | Where | Notes |
|--------------|--------|--------|
| Governed stack layout (ports, tunnel) | `docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md` | Required to reach Plan-Gate from WSL |
| Context Layer install/run | `packaging/motadata-context-layer/README.md` | Required for export |
| Stage 3 loop burn-in (pytest) | `docs/validation/STAGE3_BURN_IN_REPORT.md` | **Recommended** program hygiene; **not** a hard blocker for HTTP scenario runs (different layer) |

### What this pack does *not* validate

| Item | Status |
|------|--------|
| Final production / Action 14 closure | ✗ |
| Full host-profile matrix | ✗ |
| `Stage3LoopController` in IDE product path | ✗ (see tracker **§6.20** / burn-in doc) |

### Suggested story arc

```
A1 → A2 → D2 (ambiguity / honesty) → C1
```

(Adjust order; keep **D2** for weak-evidence behavior.)

---

## 2) Environment and commands

### 2.1 Canonical paths (WSL — adjust user if not `root`)

| Variable | Example value |
|----------|----------------|
| `M_CODER_ROOT` | `/root/Harshil-PoCs/m-coder` |
| `MOTADATA_ROOT` | `/home/harshil/Projects/Motadata` |

**GPU dev host (reference):** Plan-Gate + vLLM often run on a separate Linux machine; **WSL** reaches them via **SSH tunnel** or **LAN URL** — not assumed on `127.0.0.1` inside WSL unless you forwarded that port into WSL.

### 2.2 Service topology

```
WSL                                    GPU (or tunneled localhost)
├─ Motadata checkout (MOTADATA_ROOT)   ├─ Plan-Gate :8089
├─ Context Layer :8091                 └─ vLLM :8000 (Explain/Debug only)
└─ m-coder (M_CODER_ROOT)
```

### 2.3 Ports and URLs (set before scenarios)

```bash
export M_CODER_ROOT="${M_CODER_ROOT:-/root/Harshil-PoCs/m-coder}"
export MOTADATA_ROOT="${MOTADATA_ROOT:-/home/harshil/Projects/Motadata}"
export CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
# Plan-Gate must be reachable FROM WSL (tunnel to GPU, or LAN IP):
export PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
export VLLM_URL="${VLLM_URL:-http://127.0.0.1:8000}"
```

**Reachability rule:** `curl -sS "$PLAN_GATE_URL/healthz"` must return `{"status":"ok"}` **from the same shell** you use for `curl` to Plan-Gate. If Plan-Gate runs on the GPU host only, use an SSH tunnel into WSL or set `PLAN_GATE_URL` to the forwarded base URL (see `docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md` §3).

### 2.4 Start Context Layer (WSL)

`MOTADATA_ROOT` must exist and point at a **checked-out Motadata tree** the indexer can read. First export on a cold index can be slow (build cost).

From `M_CODER_ROOT` after installing the wheel or using dev tree:

```bash
cd "$M_CODER_ROOT"
export MOTADATA_ROOT
# One of:
motadata-context-layer
# or:
python3 -m runtime.context_layer_service
```

Verify:

```bash
curl -sS "$CONTEXT_URL/healthz"
curl -sS "$CONTEXT_URL/version"
```

### 2.5 Pre-flight health (all scenarios)

```bash
curl -sS "$CONTEXT_URL/healthz" && echo " ✓ Context Layer"
curl -sS "$PLAN_GATE_URL/healthz" && echo " ✓ Plan-Gate"
curl -sS "$VLLM_URL/v1/models" 2>/dev/null && echo " ✓ vLLM" || echo " ⚠ vLLM optional (Explain/Debug only)"
```

### 2.6 API contracts (this repo — no placeholder field names)

**`POST /v1/export_evidence`** (Context Layer) — body fields used by `runtime/context_layer_service/app.py`:

| Field | Required | Notes |
|-------|----------|--------|
| `workspace_root` | yes | Absolute path to repo root (use `MOTADATA_ROOT`) |
| `query` | yes | Natural-language query |
| `top_k` | no | Default **8** in service; this pack uses **12** unless you tune |

Successful **HTTP 200** body is the **`layer5.evidence_bundle.v1` object itself** (not wrapped under another key).

**`POST /v1/ask`** (Plan-Gate) — **`ask_request.v1.0`** (`runtime/ide/schemas/ask_request.v1.0.schema.json`):

| Field | Required | Notes |
|-------|----------|--------|
| `schema_version` | yes | Must be **`ask_request.v1.0`** |
| `request_id` | yes | Unique string per request |
| `timestamp_utc` | yes | ISO-8601 UTC |
| `query` | yes | Same intent as export (or refined) |
| `evidence_bundle` | yes | **Full object** from export response |
| `expected_workspace_identity_hash` | no | If set, must match bundle hash |
| `task_type` | no | **`general`** (plan-only / grounded answer) or **`EXPLAIN_DEBUG`** (needs `selected_file` + selection — see plugin doc) |
| `trace_id` | no | Correlation for logs |

There is **no** `mode: ask|debug|plan|code` field in v1. Express **ASK vs DEBUG vs PLAN vs CODE** intent **in the natural-language `query`** and in operator notes; the backend uses **`task_type`** and evidence quality gates.

### 2.7 Retrieval usefulness fields (Plan-Gate `metadata`)

On **`POST /v1/ask`**, the v1 ingest path adds two **JSON-serializable** fields beside the existing quality keys (`intent_type`, `evidence_quality`, `quality_reasons`, `dominance_metrics`, `policy_version`). They are safe to log and to diff across scenarios on WSL.

| Field | Type | Meaning |
|-------|------|---------|
| `operator_hints` | `string[]` | Short explanations keyed off `quality_reasons` (e.g. low core-AIOps share, noisy top-k, no core file in top-3). Empty when there is nothing extra to say beyond the reason codes. |
| `usefulness_metrics` | `object` | Bundle-level stats from **`evidence_bundle.entries`**: `entry_count`, `top1_retrieval_score`, min/max score and spread, counts of snippet rows anchored on query tokens vs weaker `selection_reason` values, per–file-class counts (same policy as the quality gate), and `noise_class_entry_count`. |

**How to use on WSL:** after each run, open **`ask_response.json`** (§3 / §5) and inspect `metadata.operator_hints` and `metadata.usefulness_metrics`. For example, **WEAK** or **PARTIAL** automated verdicts (**§2.10**) should often show non-empty `operator_hints` or a high `snippet_non_anchor_hits` / noisy `file_class_counts` — that confirms retrieval shape, not just LLM tone.

**Code references:** `runtime/ask_service/v1_ingest.py`, `runtime/layer5/retrieval/quality_gate.py` (`operator_hints_for_assessment`), `runtime/layer5/evidence/usefulness_metrics.py` (`bundle_usefulness_metrics`).

### 2.8 Automated contract tests (no live HTTP)

Canonical scenario IDs and **exact query strings** live in **`docs/validation/aiops_mvp_scenarios.v1.json`** (single source of truth for §4 and CI).

From repo root:

```bash
cd "$M_CODER_ROOT"
export PYTHONPATH=.
python3 -m pytest runtime/tests/test_aiops_mvp_scenario_pack.py -v
```

This validates: export-request shape (`workspace_root`, `query`, `top_k`), `ask_request.v1.0` schema for each query against the golden `layer5.evidence_bundle.v1`, and in-process Plan-Gate **`handle_ask_v1_request`** → `plan_only_response.v0.1` / `PLAN_ONLY`.

**Optional live smoke** (Context Layer + Plan-Gate reachable; `MOTADATA_ROOT` must be a real checkout):

```bash
export AIOPS_MVP_LIVE=1
export MOTADATA_ROOT=/home/harshil/Projects/Motadata
# Optional overrides:
# export CONTEXT_URL=http://127.0.0.1:8091
# export PLAN_GATE_URL=http://127.0.0.1:8089
# export AIOPS_MVP_LIVE_HTTP_TIMEOUT=600   # seconds per export + ask (default 300); timeouts skip, not fail
python3 -m pytest runtime/tests/test_aiops_mvp_scenario_pack.py -v -k live_export
```

### 2.9 Scenario labels vs `task_type`

| Pack label (rubric) | Typical `task_type` | Notes |
|---------------------|---------------------|--------|
| ASK / PLAN / DEBUG / CODE scenarios | `general` | Plan-only / grounded response from evidence |
| Explain/Debug with selection | `EXPLAIN_DEBUG` | Requires `selected_file`, `client_context.selection` — use plugin or construct JSON like production |

### 2.10 Batch run (all 8 scenarios + machine summary)

Runs every scenario from **`aiops_mvp_scenarios.v1.json`**, writes **`docs/validation/artifacts/aiops_mvp/scenario_<ID>/`** (same files as §3), and emits **`summary/run_summary.json`** and **`summary/run_summary.md`** with an **automated** verdict per row (`PASS` / `PARTIAL` / `FAIL` / `ERROR`) derived from Plan-Gate **`metadata.evidence_quality`**. Per-scenario **`ask_response.json`** still contains full **`metadata`** including **`operator_hints`** and **`usefulness_metrics`** (**§2.7**) for retrieval-usefulness review. That summary is a **quick signal**, not a substitute for human **`judgement.txt`** and **§6** when filling **`AIOPS_MVP_FINAL_REPORT_TEMPLATE.md`**.

```bash
cd "$M_CODER_ROOT"
export MOTADATA_ROOT=/home/harshil/Projects/Motadata
export CONTEXT_URL=http://127.0.0.1:8091
export PLAN_GATE_URL=http://127.0.0.1:8089
export AIOPS_MVP_LIVE_HTTP_TIMEOUT=600   # optional
./scripts/run_aiops_mvp_scenario_pack.sh
# One scenario only: ./scripts/run_aiops_mvp_scenario_pack.sh --scenario A1
# Stop on first HTTP error: ./scripts/run_aiops_mvp_scenario_pack.sh --fail-fast
```

---

## 3) Standard execution pattern (copy-paste)

**Queries:** use the strings in **`docs/validation/aiops_mvp_scenarios.v1.json`** (or §4 below; they must match). **`export_request.json` audit snippet (§3 tail)** requires **`$BASE`** from the same block — run it immediately after the heredocs above, not in a fresh shell without `SCENARIO_ID` / `BASE` set.

Set `SCENARIO_ID` (e.g. `A1`) and paste the exact matching query from section 4 into `QUERY`.

```bash
cd "$M_CODER_ROOT"
SCENARIO_ID="A1"
QUERY='In the Motadata repo, where does alert correlation logic likely live, and which modules appear involved in deriving correlation keys from incoming events?'
BASE="docs/validation/artifacts/aiops_mvp/scenario_${SCENARIO_ID}"
mkdir -p "$BASE"

printf '%s' "$QUERY" > "$BASE/request.txt"

# 1) Export evidence (raw bundle = HTTP 200 body)
python3 << PY
import json, urllib.request
req = {
    "workspace_root": __import__("os").environ.get("MOTADATA_ROOT", ""),
    "query": open("$BASE/request.txt", encoding="utf-8").read().strip(),
    "top_k": 12,
}
body = json.dumps(req).encode("utf-8")
r = urllib.request.Request(
    __import__("os").environ["CONTEXT_URL"].rstrip("/") + "/v1/export_evidence",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(r, timeout=600) as resp:
    bundle = json.load(resp)
with open("$BASE/export_response.json", "w", encoding="utf-8") as f:
    json.dump(bundle, f, indent=2, ensure_ascii=False)
PY

# 2) Build ask_request.v1.0 and call Plan-Gate
REQUEST_ID="aiops-mvp-${SCENARIO_ID}-$(date -u +%Y%m%dT%H%M%SZ)"
TRACE_ID="$REQUEST_ID"

python3 << PY
import json, os, urllib.request
from datetime import datetime, timezone
base = "$BASE"
rid = "$REQUEST_ID"
tid = "$TRACE_ID"
with open(os.path.join(base, "export_response.json"), encoding="utf-8") as f:
    bundle = json.load(f)
with open(os.path.join(base, "request.txt"), encoding="utf-8") as f:
    query = f.read().strip()
ask = {
    "schema_version": "ask_request.v1.0",
    "request_id": rid,
    "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "query": query,
    "evidence_bundle": bundle,
    "task_type": "general",
    "trace_id": tid,
}
# Optional: enforce identity if bundle includes hash
h = (bundle.get("workspace_identity_hash") or "").strip()
if h:
    ask["expected_workspace_identity_hash"] = h
with open(os.path.join(base, "ask_request.json"), "w", encoding="utf-8") as f:
    json.dump(ask, f, indent=2, ensure_ascii=False)
url = os.environ["PLAN_GATE_URL"].rstrip("/") + "/v1/ask"
req = urllib.request.Request(
    url,
    data=json.dumps(ask).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=600) as resp:
    out = json.load(resp)
with open(os.path.join(base, "ask_response.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
PY

echo "Artifacts under $BASE"
```

Save `export_request.json` manually if you prefer audit of the POST body (**same shell** as above so `$BASE` is set):

```bash
python3 -c "import json,os; print(json.dumps({'workspace_root':os.environ['MOTADATA_ROOT'],'query':open('$BASE/request.txt',encoding='utf-8').read().strip(),'top_k':12},indent=2))" > "$BASE/export_request.json"
```

---

## 4) Scenario pack (8)

**Canonical file:** `docs/validation/aiops_mvp_scenarios.v1.json` — queries below must match it byte-for-byte (tests enforce the JSON).

Queries below are **fixed text** for repeatability. Replace `QUERY` in §3 or maintain per-scenario `request.txt` files.

### Quick reference

| ID | Category | Focus |
|----|----------|--------|
| A1 | ASK | Single-area grounding |
| A2 | ASK | Multi-file reasoning |
| D1 | DEBUG | Root-cause + risk (via query text; `task_type`: `general`) |
| D2 | DEBUG | Honesty under ambiguity ⚠️ |
| P1 | PLAN | Low-risk plan |
| P2 | PLAN | Conservative safety |
| C1 | CODE | Safe snippet suggestion |
| C2 | CODE | Test grounding |

### A1 — Module discovery

**Query:**  
In the Motadata repo, where does alert correlation logic likely live, and which modules appear involved in deriving correlation keys from incoming events?

### A2 — Multi-file reasoning

**Query:**  
Compare likely data flow across ingestion, normalization, and incident creation for high-cardinality alerts, and cite which files appear relevant.

### D1 — Root-cause + risk

**Query:**  
Debug hypothesis: duplicate incidents are created for repeated alerts. Based on repo evidence, where are likely duplication guards implemented and what failure points should be checked first?

### D2 — Honesty under ambiguity ⚠️

**Query:**  
I suspect a timezone mismatch in alert windowing, but I do not know the responsible module. Identify likely areas and state what evidence is missing before concluding.

*Expected:* May legitimately score **PARTIAL** / weak grounding — not a failure of the pack if the system is honest.

### P1 — Low-risk plan

**Query:**  
Propose a minimal, low-risk plan to add traceable correlation-id propagation from ingest to incident records, with rollback and validation steps.

### P2 — Conservative safety plan

**Query:**  
Provide a plan to improve noisy-alert suppression logic while preserving current critical alert pathways; identify likely files to inspect first.

### C1 — Safe code suggestion

**Query:**  
Suggest a safe, non-executed patch snippet to add guardrail logging around correlation decision branches, and point to likely insertion points from evidence.

### C2 — Test grounding

**Query:**  
Provide a minimal test skeleton to validate duplicate-incident prevention logic, grounded in likely existing test structure and related modules.

---

## 5) Artifact layout

```
docs/validation/artifacts/aiops_mvp/
├── scenario_A1/
│   ├── request.txt
│   ├── export_request.json      # optional audit
│   ├── export_response.json
│   ├── ask_request.json
│   └── ask_response.json
├── scenario_A2/
│   └── ...
└── summary/
    ├── run_summary.json         # batch script only
    └── run_summary.md
```

### Required per scenario

| File | Purpose |
|------|---------|
| `request.txt` | Exact query |
| `export_response.json` | Raw bundle from Context Layer |
| `ask_request.json` | Full `ask_request.v1.0` |
| `ask_response.json` | Plan-Gate JSON |
| `evidence_summary.md` | Operator summary of evidence |
| `operator_note.md` | One-paragraph assessment |
| `judgement.txt` | `PASS` / `PARTIAL` / `FAIL` |

---

## 6) Evaluation rubric

1. **Grounding** — Tied to evidence paths / bundle, not generic prose.  
2. **Truthfulness** — Strong claims justified; uncertainty explicit.  
3. **Usefulness** — Addresses the query.  
4. **Evidence visibility** — Files / selectors / plan steps traceable; optional cross-check **`metadata.usefulness_metrics`** (path mix, snippet anchors) vs narrative (**§2.7**).  
5. **Weak-evidence honesty** — No fake ownership; asks for scope when needed.  
6. **Multi-file** (when applicable) — Coherent cross-file narrative.

| Judgement | When |
|-----------|------|
| **PASS** | 5+ of 6 clearly met |
| **PARTIAL** | 3–4 met or important gaps |
| **FAIL** | Fewer than 3 criteria met, or confident ungrounded claims |

---

## 7) Execution checklist

| Step | Done |
|------|------|
| §2.4 Context Layer up; §2.5 health green | ☐ |
| `PLAN_GATE_URL` reachable from WSL | ☐ |
| Run §3 for each scenario ID | ☐ |
| Fill `judgement.txt` + operator notes | ☐ |
| At least one **D2** run evaluated for honesty (PARTIAL acceptable) | ☐ |
| Copy summary into `docs/validation/artifacts/aiops_mvp/summary/` | ☐ |

---

## 8) Scope guard

| Do | Don't |
|----|--------|
| Capture real JSON artifacts | Change Motadata product code for this pack |
| Use contracts in **§2.6** | Invent `mode` / `repo_path` fields not in schemas |
| Document gaps | Claim Stage 3 IDE integration |
|  | Reopen locked tracker items |

---

## 9) Related docs

| Doc | Use |
|-----|-----|
| `docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md` | WSL ↔ GPU, ports, tunnel |
| `docs/runtime/WSL_CONTEXT_LAYER_CLIENT.md` | Context Layer client behavior |
| `docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md` | Plugin / tunnel defaults |
| `docs/validation/STAGE3_BURN_IN_REPORT.md` | Stage 3 pytest burn-in (separate from this pack) |
