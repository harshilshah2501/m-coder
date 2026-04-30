# Debug path validation runbook

This document is for **actually exercising** the Ask path and **recording real JSON outputs** from **WSL** (Context Layer) with Plan-Gate + vLLM on the **GPU** as HTTP backends.

**Prerequisite stack:** [MOTADATA_DEMO_SETUP_RUNBOOK.md](MOTADATA_DEMO_SETUP_RUNBOOK.md) Phase 1 (GPU) + Phase 2 (WSL Context Layer on `:8091`). Forwards so `PLAN_GATE_URL` and `CONTEXT_URL` reach those services from WSL.

---

## Two Ask paths — why v1 matches your mental model

| Path | Flow | Motadata on GPU? |
|------|------|------------------|
| **`POST /v1/ask`** (evidence bundle) | WSL **Context Layer** runs `POST /v1/export_evidence` over **WSL `WORKSPACE_ROOT`** → you send the returned **`evidence_bundle`** to Plan-Gate. Plan-Gate validates the bundle and builds context **without reading your repo from disk on the GPU** (`handle_ask_v1_request` / `no_repo_filesystem` in response). | **No** — one canonical tree on **WSL** only; no sync mismatch risk for this path. |
| **`POST /v0/ask`** (legacy / repo-side) | Plan-Gate’s **ContextEngine** opens **`repo_root` on the server** (GPU). That path must exist **there** and be readable by the Plan-Gate user. | **Yes** (or a shared mount that looks like that path on the GPU). |

The **smooth** architecture you built is **v1**: evidence is produced **once** next to the real workspace (WSL), then shipped to Plan-Gate. The runbook previously emphasized **v0** `curl`, which **reintroduced** “clone Motadata on GPU” and permission issues — that was the wrong default for WSL validation.

**Use v1 for these debug scenarios.** Use v0 only when you explicitly need to test server-side indexing / plugin-style `repo_root` behavior.

---

## Standard environment — `docs/set-envars.sh`

```bash
source /path/to/m-coder/docs/set-envars.sh
```

| Variable | Role |
|----------|------|
| `WORKSPACE_ROOT` | Motadata root **on WSL** (default `$HOME/Harshil-PoCs/Motadata`). Used only for **`POST /v1/export_evidence`**. |
| `CONTEXT_URL` | Context Layer (default `http://127.0.0.1:8091`). |
| `PLAN_GATE_URL` | Plan-Gate (default `http://127.0.0.1:8089` when forwarded from GPU). |
| `TOP_K` | Evidence `top_k` (default `8`). |
| `QUERY` | `source docs/set-envars.sh '…'` or export before/after source. |

**v0 only (ignore for v1):** `PLAN_GATE_REPO_ROOT` — see § Optional: `POST /v0/ask`.

---

## Prerequisites (WSL)

| Requirement | Notes |
|-------------|--------|
| **Demo stack** | Phase 1 + 2 from [MOTADATA_DEMO_SETUP_RUNBOOK.md](MOTADATA_DEMO_SETUP_RUNBOOK.md). |
| **Context Layer** | `curl --connect-timeout 5 --max-time 60 -sS "$CONTEXT_URL/healthz"` OK. |
| **Plan-Gate** | `curl --connect-timeout 5 --max-time 60 -sS "$PLAN_GATE_URL/healthz"` OK (via tunnel). |
| **Motadata** | Only on **WSL** at `WORKSPACE_ROOT`. |
| **Python3 + curl** | For the primary script below and extraction snippets. |

---

## Step 1 — Query set (four types)

| # | Label | **Exact query** | **Typical `evidence_quality`** |
|---|--------|-----------------|----------------------------------|
| 1 | Strong debug | `Explain how alert correlation engine works in this repo` | `STRONG` |
| 2 | Weak debug | `Why this engine is slow?` | `WEAK` |
| 3 | Insufficient (block) | `Fix this issue` | `INSUFFICIENT` |
| 4 | No-match (block) | `Explain quantumHandler in this repo` | `NO_MATCH` |

---

## Step 2 — What to capture for **each** query

### A. Request

- [ ] **Query** string  
- [ ] Full **Ask v1.0** payload (includes `evidence_bundle`) or note “v1”  

### B. Evidence / context

- [ ] Paths from `response["context_bundle"]["files"]`  
- [ ] Optional: raw **`entries`** from export_evidence JSON (top-k)  
- [ ] File classes (§ Classification helper)  

### C. Metadata

`intent_type`, `evidence_quality`, `quality_reasons`, `dominance_metrics`, `policy_version`

### D. Response

`plan_summary`, `explain_debug` (if any), blocked vs allowed, `governance_posture`, `execution`

### E. Trace

`request_id`; saved request/response bodies; vLLM proof only if Explain/Debug hits the model (GPU logs).

---

## Primary path — `export_evidence` + `POST /v1/ask` (WSL only)

**One WSL shell. No m-coder dependency.**

### 2.1 Define `run_v1_ask` in your shell (canonical copy)

**Do not fork the bash here.** Paste the **`run_v1_ask`** function from the production verification guide — **§5.2** ([`MOTADATA_VERIFICATION_GUIDE.md#canonical-manual-ask-v1`](guides/MOTADATA_VERIFICATION_GUIDE.md#canonical-manual-ask-v1)) — so fixes stay in one place.

This runbook’s **unique** content below is the **query set**, **capture checklist**, and **v1 vs v0** notes — not a second copy of `curl`/`python3` wiring.

### 2.2 Run the 4 required queries (exact)

```bash
source docs/set-envars.sh

run_v1_ask 'Explain how alert correlation engine works in this repo' '/tmp/ask_capture_1_strong.json'
run_v1_ask 'Why this engine is slow?' '/tmp/ask_capture_2_weak.json'
run_v1_ask 'Fix this issue' '/tmp/ask_capture_3_insufficient.json'
run_v1_ask 'Explain quantumHandler in this repo' '/tmp/ask_capture_4_no_match.json'
```

### 2.3 What gets collected per query

- `<base>.json` -> final `/v1/ask` response
- `<base>.evidence.json` -> `/v1/export_evidence` output
- `<base>.ask_v1.json` -> exact ask payload sent to Plan-Gate

**Expected architecture signal:** `context_resolution.no_repo_filesystem` indicates v1 evidence-first path (no GPU repo read).

### 2.4 Model invocation proof (`EXPLAIN_DEBUG` + vLLM)

The default `run_v1_ask` helper sends **`task_type` omitted → `general`**, so Plan-Gate uses the **template planner only** — no `explain_debug`, no vLLM call. That matches the four baseline captures.

To **prove** model-backed reasoning for closure:

**Server-side:** On the GPU host, Plan-Gate must reach vLLM (same as [MOTADATA_DEMO_SETUP_RUNBOOK.md](MOTADATA_DEMO_SETUP_RUNBOOK.md)): `MOTADATA_EXPLAIN_VLLM_URL` (e.g. `http://127.0.0.1:8000`). From WSL, that is usually the **forwarded** `127.0.0.1:8000` via SSH `-L`.

**Request-side:** `ask_request.v1.0` must include `task_type: "EXPLAIN_DEBUG"`, `selected_file` (a `relative_path` from the evidence bundle), and `client_context.selection` (snippet text). The quality gate must **not** be blocked (`INSUFFICIENT` / `NO_MATCH`), or the handler returns before the reasoner runs — pick a query that retrieves **core** paths (e.g. class/method names that exist under `src/main/java/...`).

**Example query (tune to your repo):**

`Explain the flow of AlertCorrelationEngine class and how alerts are grouped`

```bash
# After: source docs/set-envars.sh

run_v1_explain_debug() {
  local out_json="$1"
  local query="$2"

  : "${WORKSPACE_ROOT:?}"
  : "${CONTEXT_URL:?}"
  : "${PLAN_GATE_URL:?}"

  local tmp_dir ev req
  tmp_dir="$(mktemp -d)"
  ev="$tmp_dir/evidence.json"
  req="$tmp_dir/ask_v1_explain.json"

  curl -sS --connect-timeout 5 --max-time 60 -X POST "${CONTEXT_URL}/v1/export_evidence" \
    -H 'Content-Type: application/json' \
    -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"$query\",\"top_k\":$TOP_K}" \
    -o "$ev"

  python3 - "$ev" "$req" "$query" <<'PY'
import datetime, json, sys, uuid

ev_path, req_path, query = sys.argv[1], sys.argv[2], sys.argv[3]
ev = json.load(open(ev_path, "r", encoding="utf-8"))
entries = ev.get("entries") or []
if not entries:
    raise SystemExit("export_evidence returned no entries; cannot set selected_file")
# Prefer first entry (rank 0); override manually if needed
ent0 = entries[0]
rel = str(ent0.get("relative_path") or "")
sn = ent0.get("snippet") if isinstance(ent0.get("snippet"), dict) else {}
selection = str(sn.get("text") or "")
ask = {
    "schema_version": "ask_request.v1.0",
    "request_id": str(uuid.uuid4()),
    "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
    "query": query,
    "task_type": "EXPLAIN_DEBUG",
    "selected_file": rel,
    "client_context": {"selection": selection},
    "evidence_bundle": ev,
}
ws_hash = ev.get("workspace_identity_hash")
if ws_hash:
    ask["expected_workspace_identity_hash"] = ws_hash
json.dump(ask, open(req_path, "w", encoding="utf-8"), indent=2)
PY

  curl -sS --connect-timeout 5 --max-time 60 -X POST "${PLAN_GATE_URL}/v1/ask" \
    -H 'Content-Type: application/json' \
    --data-binary "@$req" \
    | tee "$out_json"

  cp "$ev" "${out_json%.json}.evidence.json"
  cp "$req" "${out_json%.json}.ask_v1.json"
  rm -rf "$tmp_dir"

  echo "[INFO] saved response: ${out_json}"
  echo "[INFO] evidence + request: ${out_json%.json}.evidence.json , ${out_json%.json}.ask_v1.json"
}

run_v1_explain_debug '/tmp/ask_capture_explain_debug_vllm.json' \
  'Explain the flow of AlertCorrelationEngine class and how alerts are grouped'
```

**What to record for closure:**

| Field | Pass criterion |
|--------|----------------|
| `explain_debug` | Present; either structured fields (`summary`, `logic_flow`, …) **or** `explain_debug.error` (proves reasoner ran but vLLM failed). |
| `metadata.evidence_quality` | Must be `STRONG` or `WEAK` — if `INSUFFICIENT` / `NO_MATCH`, response is blocked and **`explain_debug` is always absent** (by design). |
| Logs (optional) | Plan-Gate / vLLM log line for same `request_id` or timestamp window. |

---

## Optional note on `/v0/ask`

`/v0/ask` is intentionally out of scope for this WSL validation runbook.

Reason: `/v0/ask` asks Plan-Gate to read `repo_root` on the server host, which creates path/permission/sync coupling with a GPU-side repo copy. Your target scenario is evidence-first (`/v1/export_evidence` on WSL + `/v1/ask`), so this runbook keeps to v1 only.

---

## Extraction snippets

Point `$OUT_JSON` at the saved Plan-Gate response (v1 or v0).

### Pretty-print metadata + files

```bash
python3 -c "
import json, sys
d=json.load(open(sys.argv[1]))
r=d.get('response',d)
md=r.get('metadata') or {}
print('request_id', r.get('request_id'))
print('intent_type', md.get('intent_type'))
print('evidence_quality', md.get('evidence_quality'))
print('quality_reasons', md.get('quality_reasons'))
print('dominance_metrics', md.get('dominance_metrics'))
for f in (r.get('context_bundle') or {}).get('files') or []:
    print('file', f.get('path'))
" "$OUT_JSON"
```

### Blocked vs allowed

```bash
python3 -c "
import json, sys
r=json.load(open(sys.argv[1])).get('response', json.load(open(sys.argv[1])))
q=(r.get('metadata') or {}).get('evidence_quality')
steps=(r.get('plan_summary') or {}).get('steps') or []
print('evidence_quality', q)
print('blocked_like', q in ('INSUFFICIENT','NO_MATCH') or len(steps)==0)
print('plan_steps_len', len(steps))
" "$OUT_JSON"
```

---

## Classification helper (no m-coder dependency)

Use path rules directly when annotating files:

- `*/src/main/java/com/mindarray/aiops/*` or `runtime/*` -> `core_aiops_code`
- `*/tests/*`, `*_test.py`, `*_spec.py` -> `tests`
- `*/logs/*`, `*.log` -> `logs`
- `*/vendor/*`, `*/node_modules/*` -> `vendor_static`
- `*.yaml|*.yml|*.json|*.toml|*.ini|*.cfg|*.conf|*.properties` -> `config`
- otherwise -> `supporting_prod_code`

---

## Output template (lab notes)

```text
=== Query 1 — Strong ===
Path: v1 (export_evidence + /v1/ask)
Query:
A. Request: (attached)
B. Evidence entries / context files:
C. metadata: ...
D. plan_summary / blocked:
E. request_id=

...
```

---

## Troubleshooting

### v1 returns 400 from `/v1/ask`

- Check `schema_version` is `ask_request.v1.0`
- Check `evidence_bundle.schema_hint` is `layer5.evidence_bundle.v1`
- If `expected_workspace_identity_hash` is set, it must match `evidence_bundle.workspace_identity_hash`

### Context Layer works but no relevant evidence

- Validate `WORKSPACE_ROOT` points to the right Motadata checkout on WSL
- Increase `TOP_K` (`export TOP_K=12`) and rerun
- Preserve outputs as-is; weak/no-match outcomes are valid signals for this validation

---

## Notes

- **Expected** `evidence_quality` values are targets; record **actual** metadata.  
- **`explain_debug`** — absent for default `general` Ask; see **§2.4** for `EXPLAIN_DEBUG` + vLLM proof.  
- GPU bring-up: [MOTADATA_DEMO_SETUP_RUNBOOK.md](MOTADATA_DEMO_SETUP_RUNBOOK.md) Phase 1.
