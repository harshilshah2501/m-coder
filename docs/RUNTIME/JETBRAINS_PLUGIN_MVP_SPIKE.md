## JetBrains Plugin MVP Spike — Runtime-Governed Commit Flow

### 1. Overview

- **Purpose**: Provide a minimal JetBrains (IntelliJ) plugin that routes IDE **commit** actions through the local Plan-Gate runtime, in **shadow mode**, to validate touch-and-feel of governed enforcement without blocking developers.
- **Scope**:
  - Intercept **VCS commit** only for the MVP; push interception is optional/stubbed.
  - Build `ide_event` and `PlanRequest v0.1` compatible payloads.
  - Call local Plan-Gate service (`POST /v0/plan`) and surface `DecisionResponse v0.1` as:
    - **Runtime would block** (REFUSAL).
    - **Runtime would conditionally block / bounded-allow** (CONDITIONAL_BLOCK / BOUNDING).
    - **Runtime would allow** (APPROVE).
  - Operate in **shadow mode** only: no IDE action is actually blocked.
- **Out of scope**:
  - Model worker integration.
  - Execution sandbox tooling.
  - Retrieval / RAG UI.
  - Autonomous agent loop in the plugin.
  - Code-edit automation or refactoring tools.

This spike instantiates the IDE side of M3.4 (“IDE Plugin Integration”) against the existing Plan-Gate emulator and schemas without redefining runtime contracts.

---

### 2. Plugin responsibilities

- **Intercept commit**:
  - Hook into JetBrains VCS commit flow via `CheckinHandlerFactory` / `CheckinHandler`.
  - Capture basic repo and user context (project name, repo root, branch, revision, user).
- **Normalize to IDE/runtime contracts**:
  - Construct `ide_event` per `runtime/ide/schemas/ide_event.v0.1.schema.json` (plus `revision` in `ide_context`).
  - Wrap `ide_event` into `PlanRequest v0.1` per `runtime/ide/schemas/plan_request.v0.1.schema.json`.
- **Call Plan-Gate**:
  - POST to `http://127.0.0.1:8089/v0/plan` (Plan-Gate Service v0.1).
  - Operate in `mode: "shadow"` and `client_policy.fail_closed_if_gate_unreachable: false`.
- **Render decision in IDE**:
  - Parse `DecisionResponse v0.1` and map decisions to notifications:
    - `REFUSAL` → error-style “runtime would block this commit”.
    - `CONDITIONAL_BLOCK` / `BOUNDING` → warning-style “runtime would conditionally block / bounded-allow this commit”.
    - `APPROVE` → informational “runtime would allow this commit” (or silent).
  - Never block the commit; shadow mode is log/UX-only.
- **Emit decision logs**:
  - Append a line per decision to `~/.motadata-ai/plugin-decisions.log`:
    - `timestamp | action=commit | decision=... | repo=... | branch=... | revision=...`.

---

### 3. Commit interception flow

**Extension points and classes**

- `plugin.xml`:
  - Declares `checkinHandlerFactory` → `ai.motadata.plugin.vcs.MotadataCheckinHandlerFactory`.
  - Registers notification group `Motadata AI` for IDE notifications.
- `MotadataCheckinHandlerFactory`:
  - Creates `MotadataCheckinHandler` for each VCS commit panel.
- `MotadataCheckinHandler`:
  - Overrides `beforeCheckin()` to invoke the runtime-governed path.

**Runtime flow**

1. Developer initiates a commit in the IDE.
2. JetBrains calls `MotadataCheckinHandler.beforeCheckin()`.
3. Handler invokes `PlanGateClient.evaluateCommit(project)`:
   - Builds `ide_event`:
     - `schema_version`: `ide_event.v0.1`.
     - `event_id`: UUID.
     - `timestamp_utc`: current UTC ISO-8601.
     - `ide_context`:
       - `product`: `jetbrains`.
       - `ide`: `intellij`.
       - `project`: IntelliJ project name.
       - `repo_root`: project base path.
       - `branch`: current Git branch (`GitRepositoryManager`).
       - `revision`: current HEAD SHA (`GitRepository.currentRevision` or `"unknown-revision"`).
       - `user`: OS username.
     - `action`:
       - `action_type`: `"VCS_COMMIT_INTENT"`.
       - `target`: `"vcs_commit"`.
   - Wraps into `PlanRequest`:
     - `schema_version`: `plan_request.v0.1`.
     - `request_id`: `req-<uuid>`.
     - `timestamp_utc`: same UTC timestamp.
     - `mode`: `"shadow"`.
     - `ide_event`: as above.
     - `requested_capabilities`: `["plan_and_decide"]`.
     - `client_policy.fail_closed_if_gate_unreachable`: `false`.
   - Serializes the PlanRequest to JSON (Gson) and POSTs to `/v0/plan`.
   - Parses the JSON response into:
     - `decision`: `APPROVE` / `CONDITIONAL_BLOCK` / `REFUSAL` / `BOUNDING` / `UNKNOWN`.
     - `ui.title`, `ui.message`, `ui.severity` when present.
4. Handler inspects decision and UI:
   - **REFUSAL**:
     - Show error notification:
       - Title: runtime `ui.title` or `"Runtime would block this commit"`.
       - Message: runtime `ui.message` or `"Plan-Gate decision: REFUSAL (shadow mode). Runtime would block this commit."`.
   - **CONDITIONAL_BLOCK / BOUNDING**:
     - Show warning notification:
       - Title: runtime `ui.title` or `"Runtime would conditionally block this commit"`.
       - Message: runtime `ui.message` or generic bounded-allow explanation.
   - **APPROVE**:
     - Optionally show informational notification:
       - Title: runtime `ui.title` or `"Runtime would allow this commit"`.
       - Message: runtime `ui.message` or generic approval text.
   - **UNKNOWN decision or gate failure**:
     - Show warning notification:
       - `"Plan-Gate unavailable (shadow mode)"` + error details, or
       - `"Plan-Gate returned unknown decision (shadow mode)"`.
5. Handler logs the decision via `DecisionLogger.log(...)`.
6. `beforeCheckin()` always returns `COMMIT`:
   - Commit proceeds regardless of decision; this spike is **shadow mode only**.

---

### 4. Plan-Gate call path

- **Service endpoint**:
  - `POST http://127.0.0.1:8089/v0/plan`
  - Provided by `runtime/plan_gate_service/app.py` (see `runtime/plan_gate_service/README.md`).
- **Request**:
  - `Content-Type: application/json; charset=utf-8`.
  - Body: `PlanRequest v0.1` as described above, constructed by `PlanGateClient`.
- **Response parsing**:
  - `PlanGateClient` uses Gson to parse `DecisionResponse v0.1`:
    - Reads `decision` string into an enum.
    - Reads optional `ui { title, message, severity }`.
  - **UI resilience**:
    - When `ui` is present, plugin uses it verbatim.
    - When `ui` is missing/partial, plugin falls back to:
      - `REFUSAL` → error semantics.
      - `CONDITIONAL_BLOCK` → warning semantics.
      - `APPROVE` → informational semantics.
- **Shadow-mode error handling**:
  - Any network error, non-200 HTTP status, or JSON parse failure:
    - Treated as **non-blocking**.
    - Surfaced as `"Plan-Gate unavailable (shadow mode)"` warning.
    - Commit still proceeds; mode remains log/UX-only.

---

### 5. Logging path

- **Location**: `~/.motadata-ai/plugin-decisions.log`.
- **Format**:
  - One line per decision:
  - `YYYY-MM-DDTHH:MM:SSZ | action=commit | decision=<DECISION> | repo=<repo_root> | branch=<branch> | revision=<sha>`.
- **Behavior**:
  - Directory `~/.motadata-ai` is created on first use.
  - Failures to write the log are swallowed; logging must never affect IDE behavior.
- **Usage**:
  - Provides a simple, local audit trail for the spike and M3.4 evidence.

---

### 6. Minimal test surface

- **`PlanGateClientTest`** (Kotlin, JUnit):
  - Constructs a sample `DecisionResponse v0.1` JSON with:
    - `decision = "REFUSAL"`.
    - `ui` block with `title`, `message`, `severity`.
  - Calls `PlanGateClient.parseDecisionResponse(...)` and asserts:
    - Decision enum is `REFUSAL`.
    - UI fields are mapped correctly.
- This keeps the test surface minimal while validating JSON parsing behavior independent of a live Plan-Gate instance.

---

### 7. Demo steps

**Full walkthrough:** See [JETBRAINS_PLUGIN_DEMO_GUIDE.md](JETBRAINS_PLUGIN_DEMO_GUIDE.md) for prerequisites, step-by-step instructions, verification checklist, and troubleshooting.

Summary:

1. **Start Plan-Gate service** (from repo root):
   - Ensure Python dependencies for runtime are installed.
   - Run:
     - `python -m runtime.plan_gate_service.app`
   - Confirm health:
     - `curl http://127.0.0.1:8089/healthz` → `{"status": "ok"}`.
2. **Open plugin project in IntelliJ**:
   - Open the `jetbrains-plugin/` directory as a Gradle project.
   - Let IntelliJ import the Gradle configuration.
3. **Run the IDE with the plugin**:
   - Use the Gradle `runIde` task (from `jetbrains-plugin`):
     - `./gradlew runIde`
   - A sandbox IntelliJ instance will start with the Motadata plugin enabled.
4. **Open the `m-coder` repo in the sandbox IDE**:
   - In the sandbox IDEA, open the parent project directory (`/home/harshil/Harshil-PoCs/m-coder`).
   - Ensure Git integration is active so branch/revision can be resolved.
5. **Perform a commit**:
   - Make a small change in the repo.
   - Trigger a VCS commit from the sandbox IDE.
6. **Observe runtime-driven UX**:
   - Watch for notifications from the “Motadata AI” group:
     - Error: “Runtime would block this commit” (REFUSAL).
     - Warning: “Runtime would conditionally block this commit” (CONDITIONAL_BLOCK / BOUNDING).
     - Info: “Runtime would allow this commit” (APPROVE).
   - Confirm the commit always completes (shadow mode only).
7. **Inspect logs**:
   - Check `~/.motadata-ai/plugin-decisions.log` for entries recording:
     - Timestamp, action, decision, repo, branch, revision.

This demo path validates the end-to-end wiring from JetBrains commit → `ide_event` → `PlanRequest v0.1` → Plan-Gate Service → `DecisionResponse v0.1` → IDE notifications and local decision logging, without expanding beyond the governed MVP spike scope.

---

## Repo-Aware Ask / Safe Planning (PLAN ONLY)

### 1. Overview

- **Purpose**: Add a second, plan-only capability to the JetBrains plugin: **Repo-Aware Ask / Safe Planning**.
  - Developers can ask questions about the repository (e.g., “Where is retry logic implemented?”).
  - The runtime builds a deterministic context bundle via the **ContextEngine** (M3.0 Repository Context Engine).
  - The runtime returns a **PlanOnlyResponse** with context provenance and a short, read/inspect-only plan.
  - No execution, sandboxing, code edits, or model autonomy are permitted.
- **Position in roadmap**:
  - This is a **pre-sandbox** slice that lands **before M3.2 Execution Sandbox**.
  - It exercises repository understanding and safe planning posture without introducing execution paths.

---

### 2. Ask request/response contracts

#### 2.1 AskRequest v0.1 (plugin → runtime)

- **Location**: `runtime/ide/schemas/ask_request.v0.1.schema.json`.
- **Shape**:
  - `schema_version`: `ask_request.v0.1`.
  - `request_id`: unique string (UUID-style).
  - `timestamp_utc`: ISO-8601 UTC.
  - `repo_root`: absolute repo root path (from IDE project base path).
  - `revision`: VCS revision / HEAD SHA (for determinism).
  - `query`: developer’s question text.
  - `selected_file` (optional): currently focused file relative to `repo_root`.
  - `branch` (optional): current branch name.
  - `client_context` (optional): IDE/plugin metadata (non-semantic).
- **Determinism**:
  - Same `repo_root`, `revision`, `query`, and `selected_file` → same `ContextBundle.items` order and `selection_reason` values, per `ContextEngine` guarantees.

#### 2.2 PlanOnlyResponse v0.1 (runtime → plugin)

- **Location**: `runtime/ide/schemas/plan_only_response.v0.1.schema.json`.
- **Shape**:
  - `schema_version`: `plan_only_response.v0.1`.
  - `request_id`: echoes AskRequest.
  - `timestamp_utc`: response time in ISO-8601 UTC.
  - `context_bundle`:
    - `revision`: repo revision used when building the bundle.
    - `files[]`:
      - `path`: repo-relative file path (e.g., `billing/retry.py`).
      - `selection_reason`: deterministic reason (e.g., `symbol:retry`, `direct`, `imports`, `siblings`).
    - `selectors_used[]`: ordered list of selectors that participated (e.g., `["direct", "siblings", "imports", "symbols"]).
  - `plan_summary`:
    - `steps[]`: 3–6 short, read/inspect-only steps.
    - `notes[]` (optional): caveats or additional guidance.
  - `governance_posture`: **fixed** to `PLAN_ONLY` for this MVP slice.
  - `execution`: **boolean, hard-coded `false`**.
  - `ui`:
    - `title`: string.
    - `message`: short summary.
    - `severity`: `"info"` or `"warning"`.
- **Invariants**:
  - `execution == false` for all `/v0/ask` responses.
  - `governance_posture == "PLAN_ONLY"` for this first implementation.
  - No tool/sandbox/model execution is triggered as a side-effect of `/v0/ask`.

---

### 3. Runtime Ask path (`/v0/ask`)

#### 3.1 Endpoint

- Extended Plan-Gate service (`runtime/plan_gate_service/app.py`) with a **sidecar** path:
  - `POST /v0/ask` — AskRequest v0.1 → PlanOnlyResponse v0.1.
  - Shares the same local daemon and port as `/v0/plan` (default `127.0.0.1:8089`).
  - Implemented via `runtime.ask_service.handlers` and `runtime.ask_service.planner`.

#### 3.2 Mapping AskRequest → ContextRequest

- `runtime/ask_service/handlers.py`:
  - Validates AskRequest against `ask_request.v0.1.schema.json`.
  - Constructs a `ContextRequest`:
    - `task_id`: `request_id` or a stable default.
    - `root_path`: `repo_root`.
    - `revision`: `revision`.
    - `files`: `[selected_file]` if provided; otherwise `[]`.
    - `symbol_hints`: simple, deterministic hints extracted from `query`:
      - Split on non-alphanumeric characters.
      - Lowercase.
      - Keep tokens with length ≥ 3.
      - Deduplicate in order of first appearance.
    - `max_files`, `max_bytes`, `selectors`: defaults from `ContextRequest` / `ContextEngine`.
  - Calls `ContextEngine.build_context_bundle(request)` to produce a deterministic `ContextBundle`.
- Error handling:
  - `ContextEngineError` / `MissingExplicitFilesError` produce a **PlanOnlyResponse error variant**:
    - Empty `files`.
    - `selectors_used = []`.
    - `plan_summary.steps = []`, with a `notes[]` entry explaining the failure.
    - Still `governance_posture = PLAN_ONLY`, `execution = false`.

#### 3.3 PlanOnlyPlanner (no execution)

- Location: `runtime/ask_service/planner.py`.
- `PlanOnlyPlanner.plan(query, bundle)`:
  - Deterministically derives:
    - A primary token from the query (longest alphanumeric token, lowercased).
    - Up to 3 top context file paths from the bundle.
  - Produces **3–6** read/inspect-only steps, such as:
    - `Open billing/retry.py and scan for logic related to "retry".`
    - `Review neighboring context files: billing/jobs.py, billing/config.py.`
    - `Search the repository for usages of "retry" to locate related call sites and configuration.`
    - `Trace the control flow from the entry points you find to understand how the behavior is orchestrated.`
  - Steps are purely **inspective**:
    - No tool or sandbox invocations.
    - No code edits.
    - No model-controlled state transitions.
- Output:
  - `PlanSummary.steps`: deterministic list of steps; truncated to at most 6.
  - No execution fields; execution is enforced at the response level (`execution=false`).

#### 3.4 Building PlanOnlyResponse

- `handle_ask_request()` builds the final `PlanOnlyResponse v0.1`:
  - `context_bundle`:
    - `revision`: from `ContextBundle.revision`.
    - `files[]`: from `ContextBundle.items` (`path`, `selection_reason`).
    - `selectors_used[]`: from `ContextBundle.provenance.selectors`.
  - `plan_summary.steps`: from `PlanOnlyPlanner.plan(...)`.
  - `governance_posture`: `"PLAN_ONLY"`.
  - `execution`: `false`.
  - `ui`:
    - Successful case: `"Repo-Aware Plan (PLAN ONLY)"` title, info severity.
    - Error case: `"Repo-Aware Ask failed (PLAN ONLY)"` title, warning severity.

---

### 4. Plugin Ask UI and flow

#### 4.1 Ask Motadata AI action

- **Action**: `ai.motadata.plugin.actions.AskMotadataAiAction` registered in `plugin.xml`:
  - Added to `ToolsMenu` as “Ask Motadata AI”.
- **UI layout**:
  - Step 1: Show input dialog in the IDE:
    - Prompt: “Enter a question about this repository (PLAN ONLY, no execution):”.
    - User types the question (e.g., “Where is retry logic implemented?”).
  - Step 2: After receiving `PlanOnlyResponse v0.1`, show a read-only results dialog:
    - **PLAN ONLY badge** at the top:
      - Text: `PLAN ONLY — No execution performed`.
    - **Context bundle section**:
      - Header: `Context bundle @ <revision>`.
      - List of files:
        - `- billing/retry.py (reason: symbol:retry)`
        - `- billing/jobs.py (reason: imports)`
    - **Selectors used**:
      - Line like: `Selectors used: direct, siblings, imports, symbols`.
    - **Plan summary**:
      - Header: `Plan:`.
      - Numbered steps, 3–6 items.
    - Entire surface is read-only; no code edits or actions.

#### 4.2 Plugin AskClient

- Location: `jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/ask/AskClient.kt`.
- Behavior:
  - Builds AskRequest v0.1:
    - `schema_version`: `ask_request.v0.1`.
    - `request_id`: `req-ask-<uuid>`.
    - `timestamp_utc`: current UTC ISO-8601.
    - `repo_root`: `project.basePath`.
    - `revision`: HEAD SHA (via `GitRepositoryManager`).
    - `branch`: current branch (optional).
    - `query`: user question text.
  - POSTs to `http://127.0.0.1:8089/v0/ask` with JSON body.
  - Parses `PlanOnlyResponse v0.1`:
    - Enforces `governance_posture == "PLAN_ONLY"` and `execution == false`.
    - Extracts `context_bundle.revision`, `files[]`, `selectors_used[]`, and `plan_summary.steps[]`.
  - Returns an `AskResult` object to the UI layer.
- Error handling:
  - Network errors, HTTP non-200, or malformed responses:
    - Mapped to `AskResult.success = false` with an error message.
    - UI shows a non-blocking warning notification:
      - e.g., “Ask Motadata AI failed (PLAN ONLY): Ask service unavailable or returned invalid response.”.
    - **No fallback plan is generated in the plugin**.

---

### 5. Determinism guardrails

- **Context determinism**:
  - `ContextEngine` already enforces stable selection ordering and `selection_reason` via `ContextBundle`.
  - Ask handler does not reorder `ContextBundle.items` beyond mapping to response fields.
- **Symbol-hints determinism**:
  - `_extract_symbol_hints(query)` in `runtime/ask_service/handlers.py`:
    - Splits on non-alphanumeric characters.
    - Lowercases tokens.
    - Keeps tokens with length ≥ 3.
    - Deduplicates in order of first appearance.
  - No embeddings, vector search, or semantic retrieval are used.
- **Planning determinism**:
  - `PlanOnlyPlanner` uses only:
    - Query tokens.
    - First few context file paths.
  - Step templates and ordering are fixed and bounded (3–6 steps).
  - There is no non-deterministic source (e.g., randomization, model calls).

---

### 6. Demo steps (Ask / Safe Planning)

**Full walkthrough:** See [JETBRAINS_PLUGIN_DEMO_GUIDE.md](JETBRAINS_PLUGIN_DEMO_GUIDE.md) §5–§6 (Demo 1 commit flow, Demo 2 Ask flow), §7 verification, §8 troubleshooting.

Summary:

1. **Start Plan-Gate / Ask service** (from repo root):
   - `python3 -m runtime.plan_gate_service.app`
   - Confirms both `/v0/plan` and `/v0/ask` are available on `127.0.0.1:8089`.
2. **Run the plugin in a sandbox IDE**:
   - From `jetbrains-plugin/`:
     - `./gradlew runIde` (or equivalent in IDE).
3. **Open the `m-coder` repo in the sandbox IDE** and ensure Git integration is active.
4. **Trigger Ask Motadata AI**:
   - Use Tools → “Ask Motadata AI”.
   - Enter a question like “Where is retry logic implemented?”.
5. **Observe the response dialog**:
   - PLAN ONLY badge at top.
   - Context bundle section with files and selection reasons.
   - Selectors used line.
   - 3–6 read/inspect-only plan steps.
6. **Verify guardrails**:
   - No code edits or execution side-effects.
   - `/v0/ask` is the only runtime call path; no embeddings or RAG integration involved.


