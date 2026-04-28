# Pass A / Pass B / Pass C Setup Verification

**Purpose:** Verify the full setup and behavior for:
- Pass A (answer shaping hygiene)
- Pass B (deterministic CIG v1 graph build + CI smoke)
- Pass C (optional graph-to-answer wiring with safe fallback)

This runbook is command-first and WSL-oriented.

---

## 1) Preconditions

Run from `m-coder` repo root:

```bash
cd /home/harshil/Harshil-PoCs/m-coder
```

Set Motadata workspace root (update path if yours differs):

```bash
export MOTADATA_REPO_ROOT="/home/harshil/Harshil-PoCs/Motadata"
```

Sanity checks:

```bash
test -d "$MOTADATA_REPO_ROOT" && echo "OK: Motadata workspace found"
test -f "runtime/scripts/build_code_intelligence_graph.py" && echo "OK: CIG builder present"
```

If `mcoder` is not on PATH, use python entrypoint:

```bash
alias mcoder-local='PYTHONPATH=. python3 runtime/mcoder_cli/cli.py'
```

---

## 2) Service Health Verification

Check Context Layer and Plan-Gate:

```bash
mcoder health --auto-fix
```

If `mcoder` command is unavailable:

```bash
PYTHONPATH=. python3 runtime/mcoder_cli/cli.py health --auto-fix
```

Expected:
- Context Layer health = OK
- Plan-Gate health = OK

Hard stop if either remains down.

---

## 3) Pass A Verification (Formatting + Fallback Baseline)

Run baseline prompts (pre-graph expectation is cleaner wording, may still be anchor-heavy):

```bash
mcoder prompt "Explain the API layer architecture."
mcoder prompt "How does mail server configuration work?"
mcoder prompt "Find all classes that handle notifications."
mcoder prompt "How are config stores organized?"
```

Fallback command variant:

```bash
PYTHONPATH=. python3 runtime/mcoder_cli/cli.py --timeout-sec 20 prompt "Explain the API layer architecture."
PYTHONPATH=. python3 runtime/mcoder_cli/cli.py --timeout-sec 20 prompt "How does mail server configuration work?"
PYTHONPATH=. python3 runtime/mcoder_cli/cli.py --timeout-sec 20 prompt "Find all classes that handle notifications."
PYTHONPATH=. python3 runtime/mcoder_cli/cli.py --timeout-sec 20 prompt "How are config stores organized?"
```

Pass A check:
- Output is readable and concise
- No raw snippet blobs in default human output
- If graph payload absent, behavior remains stable (fallback path)

---

## 4) Pass B Verification (Deterministic CIG v1)

### 4.1 Build graph artifacts

```bash
PYTHONPATH=. python3 runtime/scripts/build_code_intelligence_graph.py \
  --workspace-root "$MOTADATA_REPO_ROOT" \
  --out-dir runtime/.cache/code_intelligence_graph
```

Expected printed lines include:
- `graph_jsonl: .../code_intelligence_graph.v1.jsonl`
- `graph_manifest: .../code_intelligence_graph.v1.manifest.json`
- `graph_adjacency: .../code_intelligence_graph.v1.adjacency.json`
- `graph_stats: {...}`

### 4.2 Validate artifacts exist

```bash
test -f runtime/.cache/code_intelligence_graph/code_intelligence_graph.v1.jsonl && echo "OK: jsonl"
test -f runtime/.cache/code_intelligence_graph/code_intelligence_graph.v1.manifest.json && echo "OK: manifest"
test -f runtime/.cache/code_intelligence_graph/code_intelligence_graph.v1.adjacency.json && echo "OK: adjacency"
```

### 4.3 Validate manifest schema and counts

```bash
python3 - <<'PY'
import json
p="runtime/.cache/code_intelligence_graph/code_intelligence_graph.v1.manifest.json"
m=json.load(open(p))
print("schema_version:", m.get("schema_version"))
print("node_count:", m.get("stats",{}).get("node_count"))
print("edge_count:", m.get("stats",{}).get("edge_count"))
assert m.get("schema_version")=="code_intelligence_graph.v1"
assert int(m.get("stats",{}).get("node_count",0))>0
assert int(m.get("stats",{}).get("edge_count",0))>0
print("OK: manifest checks passed")
PY
```

### 4.4 Determinism check (build twice, same hash)

```bash
HASH1=$(python3 - <<'PY'
import json
print(json.load(open("runtime/.cache/code_intelligence_graph/code_intelligence_graph.v1.manifest.json")).get("content_hash",""))
PY
)

PYTHONPATH=. python3 runtime/scripts/build_code_intelligence_graph.py \
  --workspace-root "$MOTADATA_REPO_ROOT" \
  --out-dir runtime/.cache/code_intelligence_graph >/tmp/cig_build_2.log

HASH2=$(python3 - <<'PY'
import json
print(json.load(open("runtime/.cache/code_intelligence_graph/code_intelligence_graph.v1.manifest.json")).get("content_hash",""))
PY
)

echo "HASH1=$HASH1"
echo "HASH2=$HASH2"
test "$HASH1" = "$HASH2" && echo "OK: deterministic content_hash"
```

### 4.5 CI smoke target

```bash
make cig-smoke
```

Expected:
- smoke test passes
- no-collapse traversal invariant covered

---

## 5) Pass C Verification (Optional Graph Wiring)

Pass C must be optional/additive:
- graph present -> enriched response composition
- graph missing/invalid -> Pass A fallback

### 5.1 Graph-present product checks

Run:

```bash
mcoder prompt "Explain the API layer architecture."
mcoder prompt "How does mail server configuration work?"
mcoder prompt "Find all classes that handle notifications."
mcoder prompt "How are config stores organized?"
```

Acceptance bar:

`Explain the API layer architecture.`
- mentions `APIServer`
- mentions `AbstractAPI`
- mentions concrete API handlers/extensions
- not only `APIServer.start`

`How does mail server configuration work?`
- mentions `MailServerConfiguration.beforeUpdate`
- includes lifecycle/store/collaborator flow when graph evidence exists

`Find all classes that handle notifications.`
- shows primary owner + collaborators when graph resolves them
- not single-owner collapse unless only one node is available

`How are config stores organized?`
- explains `AbstractConfigStore`
- includes read/write/store relationship when present in graph evidence

### 5.2 Fallback behavior check (graph disabled)

Temporarily move graph cache:

```bash
mv runtime/.cache/code_intelligence_graph runtime/.cache/code_intelligence_graph.bak
```

Run one prompt:

```bash
mcoder prompt "Explain the API layer architecture."
```

Expected:
- command still succeeds
- response falls back to Pass A logic (no crash, no schema break)

Restore cache:

```bash
mv runtime/.cache/code_intelligence_graph.bak runtime/.cache/code_intelligence_graph
```

---

## 6) Focused Test Suite Commands

Run all relevant tests:

```bash
PYTHONPATH=. pytest -q \
  runtime/tests/test_answer_shaping_pass_a.py \
  runtime/tests/test_code_intelligence_graph_v1.py \
  runtime/tests/test_code_intelligence_graph_smoke.py \
  runtime/tests/test_graph_traversal_payload.py \
  runtime/tests/test_ask_v1_ingest.py
```

Expected:
- all pass
- no regressions to contract behavior

---

## 7) Failure Triage

If output is still mostly:
- `main anchor for this behavior`

check in order:
1. Graph artifacts exist and manifest counts > 0
2. `content_hash` stable across rebuild
3. Ask response contains optional `graph_traversal` field
4. CLI shaping receives and prefers graph payload when present
5. Services are healthy (`mcoder health`)

Quick inspect command for Ask JSON:

```bash
python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root "$MOTADATA_REPO_ROOT" \
  --query "Explain the API layer architecture." \
  --print json | python3 -m json.tool | rg "graph_traversal|flow_paths|inheritance|owners|collaborators"
```

---

## 8) Non-Negotiables

During verification:
- Do not change retrieval/ranking logic.
- Do not change Plan-Gate contracts or schemas.
- Do not change governance posture.
- Keep graph integration optional and additive.

Invariant:

`Repo is truth. Graph is map. LLM is narrator. Runtime is judge.`

