# Pass A / Pass B / Pass C Verification (Split Setup)

This guide is for your real topology:

- **WSL:** has `Motadata` repo, runs `mcoder` CLI and Context Layer
- **GPU:** has `m-coder` repo, runs Plan-Gate
- **WSL <-> GPU:** connected by SSH tunnel (`127.0.0.1:8089`)

Core invariant:

`Repo is truth. Graph is map. LLM is narrator. Runtime is judge.`

---

## 1) Topology and Where Commands Run

Use this legend in the rest of the guide:

- **[WSL]** run inside WSL shell
- **[GPU]** run on GPU host shell
- **[WSL->GPU]** run from WSL but executes on GPU via `ssh ...`

Do not run `m-coder` source-path commands on WSL if WSL does not have the `m-coder` repo checkout.

---

## 2) Executable Generation and Installation

### 2.1 Build wheel (from m-coder repo)

**[m-coder host]**

```bash
cd ~/Harshil-PoCs/m-coder/packaging/mcoder-suite
python3 -m build --wheel -o dist
ls -1 dist/mcoder_suite-*.whl
```

### 2.2 Install wheel on WSL (CLI runtime env)

Copy wheel from GPU to WSL (example):

**[WSL]**

```bash
mkdir -p ~/tmp/mcoder-wheel
scp harshil@45.195.82.10:~/Harshil-PoCs/m-coder/packaging/mcoder-suite/dist/mcoder_suite-*.whl ~/tmp/mcoder-wheel/
pip install --force-reinstall ~/tmp/mcoder-wheel/mcoder_suite-*.whl
which mcoder
mcoder version
```

### 2.3 Split topology deployment rule (WSL + GPU)

If WSL has Motadata and GPU runs Plan-Gate:

1) Install/reinstall wheel on WSL (CLI/Context side).
2) Use `governed_services.sh` on GPU as the primary deployment/restart path.
3) Do not make ad-hoc GPU `pip install` part of normal verification flow.

### 2.4 GPU governed deployment (primary path)

**[GPU]**

```bash
cd ~/Harshil-PoCs/m-coder
./scripts/governed_services.sh status
./scripts/governed_services.sh restart
```

If your script uses different verbs, run the equivalent status/restart actions.

### 2.5 Break-glass GPU module check (debug only)

Use only for incident debugging (not normal flow):

**[GPU]**

```bash
python3 - <<'PY'
import runtime.ask_service.graph_traversal_payload as m
print("OK:", m.__file__)
PY
```

---

## 3) Service Bring-up (Split)

### 3.1 Context Layer on WSL

**[WSL]**

```bash
mcoder --verbose health --auto-fix
```

Expected: Context Layer health OK.

### 3.2 Plan-Gate on GPU

Ensure Plan-Gate is running via `governed_services.sh` on GPU.

### 3.3 SSH tunnel from WSL

Primary path: let `mcoder` manage tunnel/bootstrap.

**[WSL]**

```bash
mcoder bootstrap
mcoder stack check --json
```

If tunnel is still missing, use manual fallback.

Manual fallback:

**[WSL]** (keep this terminal open):

```bash
ssh -N -L 8089:127.0.0.1:8089 harshil@45.195.82.10
```

In another WSL terminal:

```bash
ss -ltnp | rg 8089
curl -sS -i http://127.0.0.1:8089/healthz
```

Expected:
- listener owned by `ssh`
- `/healthz` returns `200`

### 3.4 Commit parity check (WSL + GPU)

Before runtime acceptance, ensure both sides are on the same m-coder commit.

**[WSL]**

```bash
cd ~/Harshil-PoCs/m-coder
git rev-parse HEAD
```

**[GPU]**

```bash
cd ~/Harshil-PoCs/m-coder
git rev-parse HEAD
```

Expected:
- both hashes are identical for the verification run.

---

## 4) Pass B Build (Where Motadata Exists)

Because WSL has Motadata and GPU hosts Plan-Gate, build CIG where Motadata is readable, then sync artifacts to GPU.

### 4.1 Build CIG artifacts from Motadata

If WSL has runtime module available:

**[WSL]**

```bash
python3 -m runtime.scripts.build_code_intelligence_graph \
  --workspace-root /root/Harshil-PoCs/Motadata \
  --out-dir /tmp/code_intelligence_graph
```

If WSL does not have runtime module, run build on host that has both builder code and Motadata access.

### 4.2 Validate artifact set

**[WSL]**

```bash
test -f /tmp/code_intelligence_graph/code_intelligence_graph.v1.jsonl && echo "OK: jsonl"
test -f /tmp/code_intelligence_graph/code_intelligence_graph.v1.manifest.json && echo "OK: manifest"
test -f /tmp/code_intelligence_graph/code_intelligence_graph.v1.adjacency.json && echo "OK: adjacency"
```

### 4.3 Determinism check (same input -> same content_hash)

**[WSL]**

```bash
HASH1=$(python3 - <<'PY'
import json
print(json.load(open("/tmp/code_intelligence_graph/code_intelligence_graph.v1.manifest.json")).get("content_hash",""))
PY
)

python3 -m runtime.scripts.build_code_intelligence_graph \
  --workspace-root /root/Harshil-PoCs/Motadata \
  --out-dir /tmp/code_intelligence_graph >/tmp/cig_rebuild.log

HASH2=$(python3 - <<'PY'
import json
print(json.load(open("/tmp/code_intelligence_graph/code_intelligence_graph.v1.manifest.json")).get("content_hash",""))
PY
)

echo "HASH1=$HASH1"
echo "HASH2=$HASH2"
test "$HASH1" = "$HASH2" && echo "OK: deterministic content_hash"
```

### 4.4 Sync artifacts to GPU Plan-Gate cache

**[WSL]**

```bash
tar -C /tmp -czf /tmp/code_intelligence_graph.tgz code_intelligence_graph
scp /tmp/code_intelligence_graph.tgz harshil@45.195.82.10:/tmp/
ssh harshil@45.195.82.10 '
  mkdir -p ~/Harshil-PoCs/m-coder/runtime/.cache &&
  rm -rf ~/Harshil-PoCs/m-coder/runtime/.cache/code_intelligence_graph &&
  tar -xzf /tmp/code_intelligence_graph.tgz -C ~/Harshil-PoCs/m-coder/runtime/.cache
'
```

### 4.5 Restart Plan-Gate on GPU

Use your existing Plan-Gate service/process restart procedure on GPU.

---

## 5) Pass C Runtime Verification (Real CLI Feel)

### 5.1 Direct probe first (WSL through tunnel)

**[WSL]**

```bash
python3 - <<'PY'
import json, urllib.request, uuid, datetime
CTX="http://127.0.0.1:8091"; ASK="http://127.0.0.1:8089"; WS="/root/Harshil-PoCs/Motadata"
Q="How are config stores organized?"
def post(url, body):
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())
ev = post(f"{CTX}/v1/export_evidence", {"workspace_root":WS,"query":Q,"top_k":8,"task_type":"general"})
resp = post(f"{ASK}/v1/ask", {"schema_version":"ask_request.v1.0","request_id":str(uuid.uuid4()),"timestamp_utc":datetime.datetime.now(datetime.UTC).isoformat(),"query":Q,"task_type":"general","evidence_bundle":ev})
gt = resp.get("graph_traversal")
ga = (resp.get("metadata") or {}).get("graph_traversal_availability")
aa = resp.get("articulated_answer") if isinstance(resp.get("articulated_answer"), dict) else {}
print("graph_traversal_present:", isinstance(gt, dict))
print("graph_availability:", ga)
print("articulated_answer_schema:", aa.get("schema_version"))
if isinstance(gt, dict):
    print("keys:", sorted(gt.keys()))
    print("flow_paths_count:", len(gt.get("flow_paths") or []))
    print("call_paths_count:", len(gt.get("call_paths") or []))
    print("inheritance_count:", len(gt.get("inheritance") or []))
    print("owners:", gt.get("owners"))
    print("collaborators:", gt.get("collaborators"))
PY
```

Expected:
- `graph_availability` is printed and distinguishes artifact state (`present` / `missing`)
- `articulated_answer_schema: articulated_answer.v0` for general Ask plan-only responses
- `graph_traversal_present` may be `False` when artifacts are missing or traversal has no relevant signal

### 5.2 CLI prompt verification

**[WSL]**

```bash
mcoder prompt "Explain the API layer architecture."
mcoder prompt "How does mail server configuration work?"
mcoder prompt "Find all classes that handle notifications."
mcoder prompt "How are config stores organized?"
```

Renderer mode check:

- Default (`MCODER_LEGACY_ASK_RENDERER` unset): unified C-style contract is active for articulated Ask output.
- Debug fallback (`MCODER_LEGACY_ASK_RENDERER=1`): legacy deterministic renderer path is active.

Quick toggle check:

```bash
unset MCODER_LEGACY_ASK_RENDERER
mcoder prompt "Explain the API layer architecture."
MCODER_LEGACY_ASK_RENDERER=1 mcoder prompt "Explain the API layer architecture."
```

Acceptance bar:

- API architecture: includes `APIServer`, `AbstractAPI`, concrete handlers/extensions; not only `APIServer.start`
- Mail config: includes `MailServerConfiguration.beforeUpdate`, lifecycle/store/collaborator flow when present
- Notifications: includes owner + collaborators when graph resolves them
- Config stores: explains `AbstractConfigStore` + read/write/store relationships when present
- Default renderer follows unified C-style constraints: 2-4 concise sentences, flow-oriented explanation; a confidence-limit sentence appears for non-routine `coverage_gaps` or weaker evidence (routine snapshot-only gaps from `reasoning_context` do not append the chain disclaimer)
- C-style unified rendering is the default when `MCODER_LEGACY_ASK_RENDERER` is unset
- If fewer than 2 grounded components are available, output is minimal and truthful (no forced/fake flow)
- CLI may print a read-only narrative block `--- explanation (read-only, evidence-bounded) ---` before legacy fallback lines
- Fallback `answer_1` / `next_step` output remains valid when narrative block is absent
- A graph-cache note may appear when Plan-Gate reports missing code-intelligence artifacts

---

## 6) CI / Smoke Tests (m-coder repo host)

Run where `m-coder` repo exists:

```bash
cd ~/Harshil-PoCs/m-coder
PYTHONPATH=. pytest -q \
  runtime/tests/test_code_intelligence_graph_smoke.py \
  runtime/tests/test_code_intelligence_graph_v1.py \
  runtime/tests/test_graph_traversal_payload.py \
  runtime/tests/test_ask_v1_ingest.py \
  runtime/tests/test_answer_shaping_pass_a.py \
  runtime/tests/test_articulated_answer.py
make cig-smoke
```

---

## 7) Failure Triage

If responses regress to anchor-only phrasing:

1. Verify tunnel and `/healthz` on `127.0.0.1:8089`
2. Verify `graph_traversal_payload.py` exists in GPU runtime
3. Verify CIG artifacts exist in GPU `runtime/.cache/code_intelligence_graph`
4. Verify probe prints `metadata.graph_traversal_availability` and confirm artifact state (`present` / `missing`)
5. If availability is `present`, verify traversal signal (`graph_traversal_present`) and traversal keys for your prompt type
6. Restart GPU Plan-Gate and retry

If fluency/shape unexpectedly regresses:

- PLAN_ONLY Ask prose is composed deterministically in Plan-Gate (`articulated_answer`); it is not vLLM output filtered by plan-gate. Over-cautious tone usually comes from composer rules or `coverage_gaps`, not model censorship.

- Verify `MCODER_LEGACY_ASK_RENDERER` is unset in shell/service environment.
- Re-run one query with and without `MCODER_LEGACY_ASK_RENDERER=1` to confirm default/legacy path split.
- Verify environment drift is not forcing stale behavior:
  - `echo "PYTHONPATH=$PYTHONPATH"`
  - `echo "MCODER_LEGACY_ASK_RENDERER=$MCODER_LEGACY_ASK_RENDERER"`

If `/v1/ask` returns `500`:
- run direct probe script from section 5.1
- collect GPU Plan-Gate traceback/logs at that timestamp

---

## 8) What Was Validated In Sandbox

Validated in this development sandbox:
- CIG build script and tests execute (`cig-smoke`, script unit tests)
- Ask response wiring compiles and tests pass
- guide command syntax verified for local portions

Not executable in this sandbox:
- your remote GPU service management and WSL-to-GPU tunnel environment specifics

