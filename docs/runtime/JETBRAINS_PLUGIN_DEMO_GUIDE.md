# JetBrains Plugin MVP — Demo Guide

Step-by-step guide to run the Motadata Runtime Governance plugin demo: **commit interception (shadow mode)**, **Repo-Aware Ask (plan-only)**, and **Explain/Debug selected code**. Use this when testing or presenting the plugin.

**Related**

| Doc | Role |
|-----|------|
| [JETBRAINS_PLUGIN_MVP_SPIKE.md](JETBRAINS_PLUGIN_MVP_SPIKE.md) | Architecture and contracts |
| [PHASE2_JETBRAINS_GOLDEN_DEMO_RESULT.md](../demo/PHASE2_JETBRAINS_GOLDEN_DEMO_RESULT.md) | Explain/Debug (Phase-2) implementation |
| [JETBRAINS_PLUGIN_RUNTIME_WIRING_FIX.md](JETBRAINS_PLUGIN_RUNTIME_WIRING_FIX.md) | Runtime wiring fix |
| [WSL_CONTEXT_LAYER_CLIENT.md](WSL_CONTEXT_LAYER_CLIENT.md) | Context Layer client / `8091` |
| [STAGE3_BURN_IN_AND_E2E_DEMO.md](../guides/STAGE3_BURN_IN_AND_E2E_DEMO.md) | Stage 3 loop burn-in + WSL→GPU governed slice (pytest + health checks) |
| [LIVE_ROADMAP_TRACKER.md](../LIVE_ROADMAP_TRACKER.md) | Canonical program status (**§1**, **§5**, **§6**, **§7**) |

**Scope note (2026-04):** This guide covers **Plan-Gate–mediated plugin demos** (commit shadow, Ask, Explain/Debug). It does **not** describe a full product request through **`Stage3LoopController`** — that integration is **not** wired through the IDE path yet; see **STAGE3** doc *Proves / does not prove* and tracker **§6.20** / **§B7**.

---

## 0. Deployment Topology (IMPORTANT)

> This demo runs in a **split environment**:

| Component                                  | Location   |
| ------------------------------------------ | ---------- |
| **m-coder repo + runtime + plugin source** | GPU server |
| **Plan-Gate service (`:8089`)**            | GPU server |
| **SSH tunnel (port forward)**              | Windows    |
| **IntelliJ (plugin execution)**            | Windows    |

### Required condition

From **Windows PowerShell**:

```powershell
curl.exe http://127.0.0.1:8089/healthz
```

Must return:

```json
{"status":"ok"}
```

**If this fails → STOP.** Plugin will not work.

---

## Deployment Modes

### Mode A — Demo Mode (current)

- GPU runtime reads repository content from a repo copy available on the GPU side.
- Ask fallback may use `ASK_DEFAULT_REPO_ROOT` when client-provided `repo_root` is not valid on the server.
- This mode is useful for controlled demos and quick validation, but it is not the final architecture target.

### Mode B — Workspace Intelligence Mode (target)

- Context Layer runs near the workspace in WSL and reads/indexes the repository where code actually lives.
- GPU Plan-Gate receives a structured context/evidence bundle rather than depending on direct repo-path access.
- GPU-side direct repository access is not required in this mode.

**Shipped pieces (align with tracker, not aspirational only):** installable wheel + HTTP — `packaging/motadata-context-layer` → `runtime.context_layer_service` on **`127.0.0.1:8091`** by default. Plan-Gate **`POST /v1/ask`** consumes `layer5.evidence_bundle.v1` when evidence-first is used.

**Evidence-first Ask (opt-in):** default plugin path may still be **`POST /v0/ask`**. Evidence-first is enabled via JVM property `motadata.ask.evidence_first` or env `MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST` (see `jetbrains-plugin/.../MotadataAskFlags.kt`; tracker **§1.1**). When ON, flow is: export evidence from Context Layer → **`/v1/ask`** with bundle.

**Windows ↔ WSL caveat:** the IDE on Windows may not reach **`127.0.0.1:8091`** in WSL without **port forwarding** or running the client in the same network namespace as the service — verify with `curl` from the **same host environment** the plugin uses (see **STAGE3** doc Part D caveat).

---

## 1. Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Repo root** | Clone or use `m-coder` with `runtime/` and `jetbrains-plugin/` at the same level. |
| **Python 3** | Used to run the Plan-Gate service. No strict version; 3.9+ typical. |
| **JDK 17** | Required for building and running the plugin. **For `runIde`:** use JDK 17 as `JAVA_HOME`; if your system has JDK 25 (or 24), the sandbox IDE can crash (see §8 troubleshooting). |
| **Gradle** | Use the wrapper in `jetbrains-plugin/`: `./gradlew` (no global Gradle needed). |

Optional: a Python venv at repo root if you prefer isolated runtime deps.

---

## 2. One-time setup

- **Runtime (Plan-Gate / Ask):** No pip install required if you run from repo root; the service uses stdlib + local `runtime` package. If you use a venv, create it at repo root and run the app module from there so `runtime` resolves.
- **Plugin:** Open `jetbrains-plugin/` in IntelliJ (or from terminal run Gradle from that directory). Sync/import Gradle when prompted.

---

## 3. Start Plan-Gate service (on GPU machine)

The plugin talks to a single HTTP service that exposes `/v0/plan`, `/v0/ask`, `/v0/execute`, and `GET /healthz`.

> For this guide's runnable flow, Section 3 is **Mode A (Demo Mode)** setup.  
> Any assumption that runtime-local filesystem access is sufficient for retrieval is demo-only, not a final architecture rule.

**On the GPU machine** (repository root):

```bash
cd /path/to/m-coder
python3 -m runtime.plan_gate_service.app
```

Defaults: host `127.0.0.1`, port **8089**. To use another port:

```bash
PLAN_GATE_PORT=9090 python3 -m runtime.plan_gate_service.app
```

(Default Plan-Gate base URL is `http://127.0.0.1:8089` in `MotadataRuntimeConfig`; override with **`-Dmotadata.plan_gate.url=...`** or env **`MOTADATA_PLAN_GATE_URL`**. If you change the service port without overriding these, the plugin will not match the server.)

### Then establish SSH tunnel (on Windows)

```powershell
ssh -N -L 8089:127.0.0.1:8089 <user>@<gpu-server>
```

Leave this session running so `localhost:8089` on Windows forwards to the GPU server’s Plan-Gate.

### Verify from Windows

```powershell
curl.exe http://127.0.0.1:8089/healthz
# Expect: {"status":"ok"}
```

---

## 4. Build plugin (GPU) → Install (Windows IntelliJ)

**Local-only alternative:** If runtime and IDE are on the same machine, you can still use **Section 4 (alt)** below (sandbox `runIde`). For the **distributed demo** (GPU + Windows), follow this section.

### Step 1 — Build plugin on GPU

```bash
cd jetbrains-plugin
./gradlew clean buildPlugin
```

Output: `build/distributions/*.zip`

### Step 2 — Copy plugin ZIP to Windows

Use `scp`, WinSCP, or a shared drive.

### Step 3 — Install in Windows IntelliJ

1. Open IntelliJ (Windows).
2. Go to **Settings → Plugins**.
3. **Remove old plugin** (important to avoid stale builds).
4. **Install from disk** → select the ZIP.
5. **Restart IntelliJ**.

### Step 4 — Open m-coder repo

Open the same repo in IntelliJ (clone or synced copy). Ensure **Git** is active (branch visible in status bar or Version Control).

---

### 4.1 Runtime connectivity sanity check (MANDATORY)

Before running the demo, from **Windows PowerShell**:

```powershell
curl.exe -i http://127.0.0.1:8089/healthz
```

Optional deeper checks:

```powershell
curl.exe -X POST http://127.0.0.1:8089/v0/plan -d "{}"
curl.exe -X POST http://127.0.0.1:8089/v0/ask -d "{}"
curl.exe -X POST http://127.0.0.1:8089/v0/execute -d "{}"
```

Expected:

- **No** connection error.
- **400** = ✅ GOOD (service is reachable; schema validation failure is expected for empty body).

---

### 4.2 Expected plugin behavior (after wiring fix)

- `GET /healthz` = **200** → plugin considers runtime **available**.
- `POST /v0/*` = **400** → plugin shows **runtime error** (e.g. schema validation), **not** “Runtime service is not available”.

You should **never** see “Runtime service is not available” unless:

- Plan-Gate is down, or
- The SSH tunnel is broken.

---

### 4 (alt). Build and run the plugin (local sandbox IDE)

If runtime and IDE are on the **same machine** (e.g. local dev):

1. From `jetbrains-plugin/`:

   ```bash
   cd jetbrains-plugin
   ./gradlew runIde
   ```

2. A sandbox IntelliJ starts with the plugin loaded. **File → Open** → m-coder root. Ensure Git is active.

---

## 5. Demo 1 — Commit interception (shadow mode)

Shows: commit → Plan-Gate → decision → notification + log; commit always proceeds (shadow mode).

1. **Ensure Plan-Gate is running** (Section 3) and the sandbox IDE has the **m-coder** project open with Git enabled.

2. **Make a small change** in the repo (e.g. add a comment in a file or create a trivial file).

3. **Commit via the IDE:**  
   **Git → Commit...** (or Ctrl+K / Cmd+K). Add a message and click **Commit**.

4. **Observe:**
   - **Notifications** (balloon or notification area) from **“Motadata AI”**:
     - **Error (red):** “Runtime would block this commit” → Plan-Gate returned `REFUSAL`.
     - **Warning (yellow):** “Runtime would conditionally block / bounded-allow this commit” → `CONDITIONAL_BLOCK` or `BOUNDING`.
     - **Info (blue):** “Runtime would allow this commit” → `APPROVE`.
   - The **commit completes** in all cases (shadow mode does not block).

5. **Inspect the decision log:**

   ```bash
   cat ~/.motadata-ai/plugin-decisions.log
   ```

   You should see lines like:  
   `timestamp | action=commit | decision=... | repo=... | branch=... | revision=...`

**Success criteria:** One notification per commit reflecting the runtime decision, commit always succeeds, and a new log line under `~/.motadata-ai/plugin-decisions.log`.

---

## 6. Demo 2 — Repo-Aware Ask (plan-only)

Shows: question → `/v0/ask` → context bundle + plan summary; no execution, no code edits.

1. **Ensure Plan-Gate is running** (Section 3) and the sandbox IDE has **m-coder** open.

2. **Open the Ask action:**  
   **Tools → Ask Motadata AI** (or search in **Help → Find Action** for “Ask Motadata AI”).

3. **Enter a question** in the dialog, e.g.:
   - “Where is retry logic implemented?”
   - “How does the Plan-Gate handle requests?”

4. **Observe the response dialog:**
   - **PLAN ONLY** badge at the top (no execution).
   - **Context bundle:** list of repository files with **selection reasons** (e.g. `direct`, `imports`, `symbols`, `siblings`).
   - **Selectors used:** e.g. `direct, siblings, imports, symbols`.
   - **Plan summary:** 3–6 short, read/inspect-only steps (no tool execution or code changes).

5. **Verify guardrails:**  
   No code edits, no commands run, no sandbox execution. Only one runtime call: `POST /v0/ask`.

**Success criteria:** Dialog shows PLAN ONLY, context files with reasons, and a bounded plan; nothing is executed.

---

## 7. Demo 3 — Explain/Debug selected code

Shows: select code in editor → Ask Motadata AI with selection → optional real reasoning (vLLM) → structured explain/debug response (Summary, Logic flow, Likely bug/risk, Evidence, Confidence/limitations) or "Reasoning unavailable" when the service is down. No execution.

**Prerequisite for real reasoning:** A vLLM-compatible HTTP completion service (e.g. vLLM on port 8000). Default URL: `http://127.0.0.1:8000`. Override with env `MOTADATA_EXPLAIN_VLLM_URL` if your service is elsewhere. If the service is not running, the plugin still shows a response with "Reasoning unavailable" and no template steps.

1. **Ensure Plan-Gate is running** (Section 3) and the sandbox IDE has **m-coder** open. For structured reasoning, start your vLLM (or compatible) service on port 8000 if desired.

2. **Select code** in the editor (e.g. a function or block in a source file).

3. **Open the Ask action:**  
   **Tools → Ask Motadata AI** (or **Help → Find Action** → "Ask Motadata AI").

4. **Observe the dialog prompt:**  
   It shows **"Explain/Debug selected code (PLAN ONLY). Optional: add a question or leave as-is."**  
   Enter an optional question (e.g. "What does this do?" or "Where might this fail?") or leave as-is and confirm.

5. **Observe the response dialog:**
   - **Title:** "Ask Motadata AI — Explain/Debug".
   - **When the reasoning service is available:** Structured sections — **Summary**, **Logic flow**, **Likely bug/risk**, **Evidence**, **Confidence / limitations** — from the model. No plan steps are substituted.
   - **When the reasoning service is unavailable:** Message "Reasoning unavailable: ..." and a note that no template steps were substituted; ensure the reasoning service is running and `MOTADATA_EXPLAIN_VLLM_URL` is set if needed.

6. **Verify guardrails:**  
   No code edits, no execution. Only one runtime call: `POST /v0/ask` with `task_type=EXPLAIN_DEBUG`, `selected_file`, and `client_context.selection`.

**Success criteria:** With code selected, the dialog shows "Explain/Debug — PLAN ONLY" and either structured explain_debug sections (when vLLM is running) or a clear "Reasoning unavailable" message (when it is not); nothing is executed.

---

## 8. Verification checklist

Before considering the demo complete:

- [ ] Plan-Gate service responds to `GET /healthz` and `GET /version`.
- [ ] Sandbox IDE opens from `./gradlew runIde` with the Motadata plugin enabled.
- [ ] m-coder is open in the sandbox with Git integration active.
- [ ] **Commit demo:** Each commit produces a “Motadata AI” notification (REFUSAL / CONDITIONAL_BLOCK or BOUNDING / APPROVE) and the commit succeeds; `~/.motadata-ai/plugin-decisions.log` has a new entry.
- [ ] **Ask demo:** “Ask Motadata AI” returns a dialog with PLAN ONLY, context bundle (files + reasons), selectors used, and 3–6 plan steps; no execution or edits.
- [ ] **Explain/Debug demo:** With code selected, "Ask Motadata AI" shows "Explain/Debug — PLAN ONLY" and either structured sections (Summary, Logic flow, etc.) when the reasoning service is running, or "Reasoning unavailable" when it is not; no execution.

---

## 9. Troubleshooting

### 🔴 "Runtime service is not available"

Now means **only**:

| Cause | Fix |
|-------|-----|
| Plan-Gate not running | Start service on GPU (Section 3). |
| SSH tunnel not active | Recreate tunnel: `ssh -N -L 8089:127.0.0.1:8089 <user>@<gpu-server>`. |
| Wrong port | Ensure 8089 on both sides. |
| Windows cannot reach localhost:8089 | Check `netstat`, firewall, tunnel process. |

### 🟡 400 / Schema validation error

- ✅ Plugin **reached** the runtime successfully.
- ❌ Request payload issue (expected in early stages or malformed requests).

### 🟡 Ask works but Submit fails

Check: `/v0/execute` reachable from Windows, payload construction, runtime permissions.

### 🟡 Nothing happens on click

Check: plugin logs (**Help → Show Log**), RuntimeBridge errors, **stale plugin install** (uninstall → reinstall ZIP → restart).

### Other

| Issue | What to check |
|-------|---------------|
| **`curl` to 8089 fails (GPU)** | Start the service from repo root; confirm port 8089 free (`lsof -i :8089`). |
| **Plugin not in sandbox (local)** | Run from `jetbrains-plugin/`: `./gradlew runIde`. |
| **No notification on commit** | Confirm Plan-Gate running and reachable; from Windows run `curl.exe http://127.0.0.1:8089/healthz`. Check **Help → Show Log** for plugin/HTTP errors. |
| **Commit fails with Unresolved reference: CommitContext** | Known IDE/Gradle classpath issue with the VCS API; see spike doc / plugin README. |
| **Ask shows error or no context** | Ensure `/v0/ask` is served. Check `curl.exe http://127.0.0.1:8089/version` from Windows. Check runtime logs. |
| **Log file missing** | Plugin creates `~/.motadata-ai/plugin-decisions.log` on first decision; ensure write permission to `~/.motadata-ai`. |
| **runIde fails: GradleJvmSupportMatrix / Java 25** | Use JDK 17: `export JAVA_HOME=/path/to/jdk17` then `./gradlew runIde`. Clear sandbox: `rm -rf jetbrains-plugin/build/idea-sandbox` if needed. |
| **runIde fails: libsecret-1.so** | On Linux/WSL install `libsecret-1-dev` or ignore if you do not need stored passwords in the sandbox. |
| **Explain/Debug shows Reasoning unavailable** | vLLM (or compatible) service must be running (default `http://127.0.0.1:8000`). Set `MOTADATA_EXPLAIN_VLLM_URL` if elsewhere. |
| **Context Layer / evidence-first fails from Windows IDE** | Service binds WSL `127.0.0.1:8091` — Windows may need forwarding or WSL-side client; see Mode B caveat above and `WSL_CONTEXT_LAYER_CLIENT.md`. |

---

## 10. Log and artifact locations

| Item | Location |
|------|----------|
| Plugin decision log | `~/.motadata-ai/plugin-decisions.log` |
| Plan-Gate service | `http://127.0.0.1:8089` (default) |
| Service code | `runtime/plan_gate_service/app.py` |
| Ask handler | `runtime/ask_service/handlers.py` |
| Plugin source | `jetbrains-plugin/src/main/kotlin/` |
| Plugin descriptor | `jetbrains-plugin/src/main/resources/META-INF/plugin.xml` |
| Explain/Debug reasoner | `runtime/ask_service/reasoner.py` |

---

## 11. Quick reference — commands

```bash
# Terminal 1 — Plan-Gate (from repo root)
cd /path/to/m-coder
python3 -m runtime.plan_gate_service.app

# Terminal 2 — Plugin sandbox (from plugin dir)
cd jetbrains-plugin
./gradlew runIde
# Then in sandbox: File → Open → m-coder repo
# Demo 1: make change → Git → Commit
# Demo 2: Tools → Ask Motadata AI → enter question (no selection)
# Demo 3: select code → Tools → Ask Motadata AI → (optional question) → Explain/Debug result
# Optional for Demo 3: start vLLM on 8000 or set MOTADATA_EXPLAIN_VLLM_URL

# Verify
curl http://127.0.0.1:8089/healthz
cat ~/.motadata-ai/plugin-decisions.log
```

---

## 12. Known real-world pitfall

**Stale plugin builds cause most issues.**

If behavior does not match expectations:

```powershell
# On GPU
./gradlew clean buildPlugin

# On Windows: uninstall plugin → reinstall ZIP → restart IntelliJ
```
