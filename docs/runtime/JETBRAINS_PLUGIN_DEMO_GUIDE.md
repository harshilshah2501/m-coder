# JetBrains Plugin MVP — Demo Guide

Step-by-step guide to run the Motadata Runtime Governance plugin demo: **commit interception (shadow mode)**, **Repo-Aware Ask (plan-only)**, and **Explain/Debug selected code**. Use this when testing or presenting the plugin.

**Related:** [JETBRAINS_PLUGIN_MVP_SPIKE.md](JETBRAINS_PLUGIN_MVP_SPIKE.md) — architecture and contracts. **Explain/Debug (Phase-2):** [PHASE2_JETBRAINS_GOLDEN_DEMO_RESULT.md](../demo/PHASE2_JETBRAINS_GOLDEN_DEMO_RESULT.md) — implementation and contracts.

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

## 3. Start the Plan-Gate service

The plugin talks to a single HTTP service that exposes both `/v0/plan` (commit flow) and `/v0/ask` (Ask flow).

1. **From the repository root** (directory that contains `runtime/` and `jetbrains-plugin/`):

   ```bash
   cd /path/to/m-coder
   python3 -m runtime.plan_gate_service.app
   ```

   Defaults: host `127.0.0.1`, port **8089**. To use another port:

   ```bash
   PLAN_GATE_PORT=9090 python3 -m runtime.plan_gate_service.app
   ```

   (The plugin is hardcoded to `127.0.0.1:8089`; if you change the port, you must change it in the plugin or run on 8089.)

2. **Confirm the service is up:**

   ```bash
   curl http://127.0.0.1:8089/healthz
   # Expect: {"status":"ok"}

   curl http://127.0.0.1:8089/version
   # Expect: JSON with service_version, supported_schemas (plan_request, decision_response, ask_request, plan_only_response, ...)
   ```

3. Leave this terminal running for the whole demo.

---

## 4. Build and run the plugin (sandbox IDE)

1. **From the `jetbrains-plugin/` directory:**

   ```bash
   cd jetbrains-plugin
   ./gradlew runIde
   ```

   Or in IntelliJ: open `jetbrains-plugin` as project, then run the **Run > runIde** (Gradle) task.

2. A **new IntelliJ instance** (sandbox) starts with the Motadata plugin already loaded. You use this instance for all demo steps.

3. **Open the m-coder repo in the sandbox:**  
   In the sandbox IDE, **File → Open** and select the **m-coder** root directory (the same repo that contains `runtime/` and `jetbrains-plugin/`).  
   Ensure the project is recognized and **Git** is active (branch name visible, e.g. in status bar or Version Control tool window).

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

| Issue | What to check |
|-------|----------------|
| **`curl` to 8089 fails** | Start the service from repo root: `python3 -m runtime.plan_gate_service.app`. Confirm no firewall and port 8089 free (`lsof -i :8089` or equivalent). |
| **Plugin not in sandbox** | Run from `jetbrains-plugin/`: `./gradlew runIde`. Confirm build succeeds and the run configuration uses the plugin module. |
| **No notification on commit** | Confirm Plan-Gate is running and reachable at `127.0.0.1:8089`. Check sandbox **Help → Show Log in Explorer/Finder** for plugin or HTTP errors. |
| **Commit fails with “Unresolved reference: CommitContext”** | Known IDE/Gradle classpath issue with the VCS API. See spike doc and plugin README; fix is in progress (e.g. correct IntelliJ platform / bundled module for your IDE version). |
| **Ask shows “error” or no context** | Ensure `/v0/ask` is served (same process as `/v0/plan`). Check `curl http://127.0.0.1:8089/version` lists `ask_request` and `plan_only_response`. Check runtime logs for Python tracebacks. |
| **Log file missing** | Plugin creates `~/.motadata-ai/plugin-decisions.log` on first decision. Ensure you have write permission to `~/.motadata-ai` (plugin may create the directory). |
| **runIde fails: GradleJvmSupportMatrix / IllegalArgumentException: 25** | IntelliJ 2023.3’s Gradle plugin cannot parse Java 25. **Workaround:** (1) Run with JDK 17: `export JAVA_HOME=/path/to/jdk17` then `./gradlew runIde`. (2) If the system has JDK 25, point `JAVA_HOME` to JDK 17 before running. (3) Clear the sandbox: `rm -rf jetbrains-plugin/build/idea-sandbox` then run `./gradlew runIde` again. |
| **runIde fails: libsecret-1.so / PasswordSafeSettings** | On Linux (e.g. WSL, minimal containers) the credential store native library may be missing. The IDE often continues with a fallback; if it still exits, install `libsecret-1-dev` (e.g. `apt install libsecret-1-dev`) or ignore if you do not need stored passwords in the sandbox. |
| **Explain/Debug shows "Reasoning unavailable" or error** | For structured Explain/Debug, a vLLM-compatible HTTP completion service must be running (default `http://127.0.0.1:8000`). Set `MOTADATA_EXPLAIN_VLLM_URL` if the service is on another URL. When the service is down, the plugin correctly shows the error and does not substitute template steps. |

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
