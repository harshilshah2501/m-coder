# Motadata AI Coding Assistant — Demo Scenarios & Success Criteria

**Purpose:** **What to demonstrate**, **how**, and **when the deployment counts as successful**. For machine setup order and commands, use [MOTADATA_DEMO_SETUP_RUNBOOK.md](MOTADATA_DEMO_SETUP_RUNBOOK.md). For architecture, use [MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md](MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md).
For **repeatable HTTP/verifier verification** (not demo talk-track), use [MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md](guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md) and [MOTADATA_SIMPLE_PATH.md](../MOTADATA_SIMPLE_PATH.md).

---

## 1. Prerequisites

Complete the runbook in order:

1. [Phase 1 — GPU](MOTADATA_DEMO_SETUP_RUNBOOK.md#phase-1--gpu-server) (gates **P1-***)
2. [Phase 2 — WSL](MOTADATA_DEMO_SETUP_RUNBOOK.md#phase-2--wsl) (gates **P2-***)
3. [Phase 3 — Windows](MOTADATA_DEMO_SETUP_RUNBOOK.md#phase-3--windows-client) (gates **P3-***)

**Operator profile this doc assumes:**

- JetBrains IDEA runs on **Windows**.
- Motadata AIOps workspace is in **WSL Linux FS** (opened via WSL backend).
- Context Layer runs in **WSL** on port **8091**.
- Plan-Gate + vLLM run on **GPU**, reached from Windows via SSH local forwards.

---

## 2. Demo talk-track (suggested order)

Use this as a **narrative** while screens are visible (IDE, WSL terminal, optional GPU terminal).

| Step | What to show | How |
|------|----------------|-----|
| 1 | **Three surfaces** | Windows IDE; WSL terminal (Context Layer); GPU/SSH (vLLM + Plan-Gate) |
| 2 | **GPU stack** | On GPU: `curl http://127.0.0.1:8000/v1/models`; then Plan-Gate `/version` shows **`ask_request_v1`** |
| 3 | **Context Layer** | `GET /healthz`, `GET /version` — call out **`evidence_schema_hint`** |
| 4 | **Evidence export** | `POST /v1/export_evidence` with Motadata **`workspace_root`** — show **`schema_hint`**, **`entries`** |
| 5 | **IDE Ask (evidence-first)** | Enable evidence-first VM options; run Ask — UI shows evidence bundle, plan steps, **PLAN ONLY** |
| 6 | **No-match query** | Query e.g. **`quantum entanglement handler in repo`** — show **true no-match** or weak lexical fill; do not hide empty evidence |
| 7 | **Failure mode** | Stop Context Layer; repeat Ask — show **controlled** fallback when unreachable vs **error** when export fails while service is up ([architecture §4.2](MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md#42-fallback-summary)) |

---

## 3. Scripted checks (copy/paste)

After runbook Phase 3, from **Windows** (with tunnel up):

```bash
curl.exe -sS http://127.0.0.1:8091/healthz
curl.exe -sS http://127.0.0.1:8089/version
curl.exe -sS http://127.0.0.1:8000/v1/models
```

If Windows `127.0.0.1:8091` is unstable but WSL-local checks pass, use WSL IP from the runbook:

```bash
curl.exe -sS http://172.30.127.150:8091/healthz
```

Expected health body:

```json
{"status": "ok", "service": "motadata_context_layer", "package_version": "0.1.0"}
```

From **WSL** (evidence API):

```bash
curl -sS -X POST http://127.0.0.1:8091/v1/export_evidence \
  -H 'Content-Type: application/json' \
  -d '{"workspace_root":"/root/Harshil-PoCs/Motadata","query":"smoke","top_k":8}'
```

Adjust **`workspace_root`** to your path.

---

## 4. Deployment success criteria

The deployment is **valid for demo / sign-off** only if **all** of the following hold:

| # | Criterion |
|---|-----------|
| 1 | From **Windows** (PowerShell): `curl.exe` to WSL Context Layer **`/healthz`** at configured URL succeeds |
| 2 | From **Windows** (PowerShell): `curl.exe` to Plan-Gate **`/version`** at **`http://127.0.0.1:8089`** succeeds **after** SSH tunnel is up |
| 3 | From **Windows** (PowerShell): `curl.exe` to vLLM **`http://127.0.0.1:8000/v1/models`** succeeds **after** the same tunnel |
| 4 | From **WSL**: **`POST /v1/export_evidence`** with real Motadata **`workspace_root`** returns **HTTP 200** and a bundle with **`schema_hint`** = **`layer5.evidence_bundle.v1`** |
| 5 | Plugin UI shows **evidence bundle** content for evidence-first Ask |
| 6 | Response metadata shows **`ask_path`** consistent with **v1 evidence** (e.g. **`v1_evidence`**) |
| 7 | On **contract failure** (bad evidence, `/v1/ask` errors) — **no** silent “success” |
| 8 | **One golden query** (known match in workspace) passes end-to-end |
| 9 | **One no-match** query — **§2 step 6** — observed |

---

## 4.1 Action 9 closure capture rule (Windows Host-A)

For the final Host-A pass, each scenario must be recorded with:

- `request_id`
- backend JSON artifact
- plugin-visible output artifact (dialog text or screenshot)
- trace references: Context Layer, Plan-Gate, and vLLM for Explain/Debug

Allowed status per scenario row: **PASS / FAIL / NOT_PROVEN**.  
Do not leave blanks; if trace correlation is missing, mark **NOT_PROVEN**.

---

## 5. Demo limitations (operator awareness)

- **Gradle `:test`** for the plugin may hit an IntelliJ sandbox **Index** error in some environments; **`compileKotlin`** / **`compileTestKotlin`** remain useful.
- Wheel may include small **golden** fixtures under `layer5/evidence/golden/` (cosmetic bloat only).
- Networking quirks: [runbook §8](MOTADATA_DEMO_SETUP_RUNBOOK.md#8-troubleshooting).
- PowerShell note: `curl` may resolve to `Invoke-WebRequest`; use `curl.exe` for runbook-compatible flags (`-sS`).

---

## 6. Automated tests (optional, GPU checkout)

```bash
cd ~/m-coder
export PYTHONPATH="$(pwd)"
python3 -m pytest runtime/tests/test_context_layer_service.py runtime/tests/test_ask_v1_ingest.py -q
```

Use as **regression** signal, not a substitute for **§4** human criteria.

---

## 7. Git reference

| Item | Value |
|------|--------|
| Branch | `feature/l5-context-layer-v1-ask-packaging` |
| Remote | `origin` (e.g. `github.com:harshilshah2501/m-coder.git`) |

---

*Update when demo script or sign-off criteria change.*
