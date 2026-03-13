# Canonical Execution Intent v1 — Design Freeze

**Status:** Design only. No implementation, no schema migration, no runtime refactor in this document.

**Purpose:** Define a canonical execution artifact so that the action evaluated by DeterministicGuard and Plan-Gate is the **same** artifact later handed to SandboxExecutor and the sandbox backend. This is a policy/execution integrity design.

**Scope:** Pre-M4.1 integrity hardening. Extends ARCHITECTURE_FREEZE_v1 and PRE_GATE_DESIGN_v1; does not replace them.

---

## 1. Purpose

Governed execution today can suffer a **policy/execution mismatch**: the runtime may evaluate one representation of an action (e.g. raw command string, or a pre-parse view) while a downstream layer materializes a different representation for execution (e.g. shell-parsed argv, path-normalized working_dir, backend-specific wrapping). If those differ, policy has not actually authorized what runs.

A **canonical execution artifact** fixes this by making a single, stable representation the sole object that:

- is normalized once from the incoming request,
- is evaluated by DeterministicGuard and Plan-Gate,
- is passed unchanged (modulo allowed equivalent transformations) to SandboxExecutor and the backend.

The artifact’s identity (canonical_hash) can then be used consistently in ledger, replay, audit, and shadow comparison.

---

## 2. Problem Statement

Policy can evaluate one representation while execution runs another when translation or mutation occurs between evaluation and execution. Concretely:

- **Argument rewriting:** Plan-Gate may see a raw command string; the handler later parses it with `shlex.split` (or equivalent) into argv. Parsing can change meaning (e.g. quoting, spaces). The argv actually executed was never evaluated by policy.
- **Path normalization:** working_dir or paths in argv might be relative at evaluation time and absolute at execution time, or normalized differently by different layers, changing what “path” policy thought it was judging.
- **Shell wrapping:** If any layer re-interprets the action as a shell command or wraps it in a shell, the executed process tree and arguments can diverge from the structured representation policy saw.
- **Backend-specific transformation:** A container driver might rewrite paths for mount mapping, or add wrapper processes; a local driver might resolve symlinks. If those changes are not provably equivalent, the executed action is not the evaluated action.
- **Container/runtime translation:** Backend may translate “run this argv” into a different invocation (e.g. exec form vs shell form, or different entrypoint). That translation must be either equivalent or re-evaluated.
- **Tool-layer materialization:** Any layer that turns an abstract or high-level description into a concrete command must produce the same canonical artifact that was (or will be) evaluated, or must treat the result as a new artifact and re-enter policy.

Without a single canonical artifact and a strict “evaluate this, execute this” invariant, we cannot guarantee that refusals or allowances apply to what actually runs.

---

## 3. Core Invariant

**Invariant (exact wording):**

- The artifact judged by DeterministicGuard and Plan-Gate **must be** the same canonical execution artifact that is later executed by SandboxExecutor and the sandbox backend.
- Downstream mutation of that artifact is **forbidden** unless:
  - **(a)** the mutation is mechanical and provably equivalent (e.g. path remapping inside a container that preserves semantics for the process), or
  - **(b)** the mutation produces a new, distinct artifact that re-enters policy evaluation (DeterministicGuard and Plan-Gate) before execution.

In other words: **same artifact in, same artifact out** from policy to execution; any change that is not provably equivalent must re-enter the chain with a new canonical artifact and new canonical_hash.

---

## 4. Proposed Artifact

**CanonicalExecutionIntent** is the single canonical representation of “what will be executed.” All policy evaluation and execution use this structure (or a strict subset/derivation that preserves identity).

### 4.1 Identity / provenance

| Field        | Type   | Description |
|-------------|--------|-------------|
| `request_id`| string | Request identifier; links to ledger and response. |
| `plan_hash` | string | Hash of the plan (or equivalent) this intent is part of. |
| `intent_id` | string | Unique id for this intent instance (e.g. UUID or request_id + sequence). |
| `canonical_hash` | string | Deterministic hash of the normalized execution content (see §6). Same artifact → same hash. |

### 4.2 Execution fields

| Field              | Type           | Description |
|--------------------|----------------|-------------|
| `executable`       | string         | Executable path or name (first element of argv). Must be normalized per §5. |
| `argv`             | list of string | **Canonical** argument vector: `[executable, arg1, arg2, ...]`. Structured argv is canonical; **shell text is not**. No shell parsing downstream. |
| `working_dir`      | string         | Absolute path to working directory. Normalized per §5. |
| `env_delta`        | dict string→string | Environment variables to set/override for this execution (delta over base env). Normalized per §5. |
| `timeout_seconds`  | int \| null    | Timeout in seconds; null means use default. |
| `capture_artifacts`| list of string | Paths (or patterns) for artifacts to capture post-execution; optional. |

**Explicit:** The canonical representation of “what runs” is **structured argv**, not shell text. No layer may treat a shell string as the source of execution truth; any shell string must be normalized to argv (by a normalizer) before becoming a CanonicalExecutionIntent.

### 4.3 Policy-relevant fields

These support DeterministicGuard and Plan-Gate without requiring them to re-parse the command:

| Field                 | Type   | Description |
|-----------------------|--------|-------------|
| `filesystem_intent`   | string or enum | Summary of filesystem intent (e.g. read_only, read_write, destructive_pattern). Optional; for guard/gate use. |
| `network_intent`     | string or enum | Summary of network intent (e.g. none, allowlisted, arbitrary). Optional. |
| `side_effect_class`   | string or enum | Classification for policy (e.g. local_only, irreversible_candidate). Optional. |
| `authority_context`   | object or dict | Authority/identity context for Plan-Gate. Optional. |
| `irreversibility_class` | string or enum | Irreversibility classification for boundary logic. Optional. |

### 4.4 Optional metadata

| Field               | Type   | Description |
|---------------------|--------|-------------|
| `backend_hint`      | string | Preferred or required backend (e.g. local, container). Optional. |
| `execution_surface` | string | Surface that created this intent (e.g. execute_service, orchestrator). Optional. |
| `notes`             | string | Non-authoritative notes; not used for hashing or policy. Optional. |

---

## 5. Normalization Rules

A **CommandNormalizer** (or equivalent) turns an incoming action/request into a CanonicalExecutionIntent. Normalization must be deterministic: same input → same output.

### 5.1 Paths

- **working_dir:** Convert to absolute path. Resolve `.` and `..`; resolve symlinks only if the normalization contract explicitly says so (and then consistently). Empty or missing → treat as request error or use a defined default (e.g. repo_root); document which.
- **executable and paths in argv:** If the design specifies “absolute paths for executables,” normalize the first element of argv to an absolute path when possible; otherwise define a stable convention (e.g. relative to working_dir). Paths that are clearly workspace-relative should be normalized against working_dir so that the same logical path always yields the same string.

### 5.2 argv

- **Input:** If the request supplies a command string, the normalizer parses it once (e.g. shlex-like) into a list of strings. That list is the only source of argv; no downstream shell parsing of the same string.
- **Canonical form:** argv is a list of strings: `[executable, arg1, arg2, ...]`. No leading/trailing whitespace in elements; no empty elements unless semantically required. Order is significant and stable.
- **Executable:** First element of argv is the executable (path or name). It must be normalized per path rules above if “executable normalization” is in scope.

### 5.3 Environment

- **env_delta:** Key-value pairs; keys and values are strings. Keys normalized (e.g. defined order or canonical key set) for hashing. No inheritance from process env in the canonical artifact—only the delta that this execution adds/overrides.

### 5.4 Working directory

- **working_dir:** Always a single absolute path string after normalization. No default in the normalizer unless specified (e.g. “default to repo_root when missing”).

### 5.5 Shell disallowance

- The canonical artifact does **not** contain a shell command string as the execution spec. Shell use, if ever supported, must be an explicit execution mode (e.g. “run with /bin/sh -c”) represented as argv `["/bin/sh", "-c", "..." ]` and normalized like any other argv; the string inside is then part of the canonical representation and hashed as-is.

### 5.6 Deterministic hashing input

- Normalization must produce a stable structure so that the same logical action always yields the same canonical_hash. All fields that contribute to canonical_hash must be normalized before hashing (see §6).

---

## 6. Hashing / Identity

**canonical_hash** is derived from the CanonicalExecutionIntent so that:

- Same artifact (after normalization) → same hash.
- Hash is computed **after** normalization; only normalized fields participate.

### 6.1 Derivation rules

- **Deterministic serialization:** Serialize the intent to a canonical form (e.g. JSON with sorted keys, fixed field order, no optional keys omitted in a way that changes meaning).
- **Stable field order:** Define a fixed order for all fields that contribute to the hash (e.g. request_id, plan_hash, intent_id, executable, argv, working_dir, env_delta, timeout_seconds, capture_artifacts, and any policy-relevant fields that are part of “what is executed”). Exclude intent_id if it is a random UUID (so that two intents with the same execution content get the same hash); include it only if intent_id is derived from content.
- **Hash algorithm:** Use a single, specified algorithm (e.g. SHA-256). Hash the serialized bytes (e.g. UTF-8).
- **Same artifact → same hash:** Any two CanonicalExecutionIntent values that represent the same execution (same normalized executable, argv, working_dir, env_delta, etc.) must produce the same canonical_hash.

### 6.2 Use of canonical_hash

- **Ledger:** Store canonical_hash on ledger rows (plan-gate decision, sandbox execution) so that every decision and execution is tied to the exact artifact evaluated and run.
- **Replay:** Replay can compare canonical_hash to ensure that replayed steps match the original intent.
- **Audit:** Auditors can verify that the executed action (reported with canonical_hash) matches the action that was allowed (same hash in decision row).
- **Shadow comparison:** Shadow runs can compare canonical_hash of baseline scenarios to production intents to ensure alignment.

---

## 7. Runtime Placement

The runtime chain is:

```
request
  → CommandNormalizer (build CanonicalExecutionIntent from request)
  → CanonicalExecutionIntent
  → DeterministicGuard (evaluate intent; hard-fail or pass)
  → Plan-Gate (evaluate intent; posture: refuse | defer | bounded_allow | safe_execute)
  → SandboxExecutor (receive same intent; execute or block)
  → SandboxDriver (receive same intent or equivalent; run or validate)
  → backend
```

### 7.1 Responsibilities

- **CommandNormalizer:** Owns parsing and normalization. Input: raw request (e.g. command string, working_dir, env, etc.). Output: CanonicalExecutionIntent. Single place where “request” becomes “canonical artifact.”
- **DeterministicGuard:** Input: CanonicalExecutionIntent. Evaluates hard-fail categories (e.g. protected branch, destructive FS, irreversible system, authority mismatch, unsupported network). Does not mutate the intent. Output: pass or refuse (with reason).
- **Plan-Gate:** Input: CanonicalExecutionIntent (or a view that includes all policy-relevant fields). Evaluates authority, boundary, irreversibility; outputs posture. Does not mutate the intent.
- **SandboxExecutor:** Input: CanonicalExecutionIntent (or a type that carries the same identity and execution fields). Passes the same artifact (or an equivalent view) to the driver. Does not rewrite executable/argv/working_dir in a way that changes meaning; may add ledger linkage or result handling.
- **SandboxDriver:** Input: execution fields from the same canonical intent (command = argv, working_dir, env from env_delta, timeout). May apply **allowed** equivalent transformations (e.g. path remapping for container mounts); see §8.
- **Backend:** Runs the process. Receives the (possibly remapped) argv and environment; must not introduce new semantics (e.g. no extra shell wrapping unless that is part of the canonical intent).

No layer between normalizer and backend may materially rewrite the intent unless the mutation is provably equivalent or the new artifact re-enters the chain.

---

## 8. Mutation Policy

### 8.1 Allowed transformations (provably equivalent)

- **Mechanical path remapping (container driver):** Mapping workspace paths to container paths (e.g. `/repo` → `/workspace`) so that the process inside the container sees the same logical paths. The remapping must be invertible and semantics-preserving for the process.
- **Workspace mount translation:** Translating working_dir and paths in argv to container mount points without changing the logical path names the process uses.
- **Backend-specific wrapper generation:** Wrappers that only set up environment or launcher and then exec the same argv (e.g. `exec "$@"`) do not change the canonical execution; the process tree that does the work must be the same argv.

For these, **canonical_hash remains unchanged**: the intent identity is preserved; only the physical location of execution changes.

### 8.2 Equivalent transformation criteria

A transformation is **equivalent** if:

- The process that actually runs has the same executable (after remap), same argv (after path remap only), same effective working directory (after remap), and same effective environment (env_delta applied). No new arguments, no shell interpretation of the argv, no change to side-effect semantics from the process’s point of view.

### 8.3 When re-evaluation is required

- If any layer changes executable, argv (beyond path remap), working_dir (beyond remap), or env_delta in a way that is not equivalent, the result is a **new** artifact. That artifact must be given a new intent_id and new canonical_hash and must **re-enter** DeterministicGuard and Plan-Gate before execution.
- If the backend cannot run the intent without a non-equivalent transformation (e.g. must convert to shell form), the implementation must either refuse or produce a new CanonicalExecutionIntent for the shell form and re-run the chain.

### 8.4 When canonical_hash must remain unchanged

- When only equivalent transformations (path remap, mount translation, exec-only wrapper) are applied. The ledger and audit trail refer to the original canonical_hash.

### 8.5 When a new artifact/hash must be created

- Whenever the execution spec (executable, argv, working_dir, env_delta) is changed in a non-equivalent way. The new artifact goes through normalization again, gets a new canonical_hash, and must pass DeterministicGuard and Plan-Gate before execution.

---

## 9. Ledger and Replay Implications

### 9.1 Ledger rows

- Plan-Gate decision rows and sandbox execution rows should reference the **canonical_hash** (and preferably request_id, plan_hash) of the CanonicalExecutionIntent that was evaluated and executed.
- Storing: canonical_hash, request_id, plan_hash, intent_id (optional), backend used (e.g. local, container), and execution result linkage (e.g. ledger_row_id for outcome) allows full provenance: “this decision/execution was for this exact intent.”

### 9.2 Replay

- Replay logic should use canonical_hash (and request_id / plan_hash as needed) to match replayed steps to original intents. Replaying the same intent implies same canonical_hash.

### 9.3 Audit evidence

- Audit evidence should include the canonical_hash so that auditors can verify that the action that was allowed (Plan-Gate row) is the same as the action that was executed (sandbox row).

### 9.4 Post-execution provenance

- Post-execution, the result (success/failure, exit code, logs) should be linked to the same canonical_hash and request_id so that provenance is end-to-end.

---

## 10. Interaction with Architecture Freeze

This design **extends** ARCHITECTURE_FREEZE_v1.md and does not invalidate it.

- The canonical execution chain in the freeze remains: Orchestrator → Plan-Gate → SandboxExecutor → SandboxDriver → Backend. This design **inserts** normalization and a canonical artifact **before** the existing chain and **tightens** the contract: the object flowing through the chain is a CanonicalExecutionIntent, and no layer may materially mutate it (except as in §8).
- The four runtime invariants (no bypass, fail-closed, governance boundary, shadow isolation) are unchanged. This design adds a **fifth** concern: execution identity (the artifact evaluated equals the artifact executed).
- Plan-Gate remains the mandatory governance gate; DeterministicGuard remains pre–Plan-Gate. They now operate on CanonicalExecutionIntent instead of ad-hoc request shapes.
- Ledger ownership and shadow role are unchanged; ledger and shadow can later store or reference canonical_hash as specified in §9.

**Placement:** This design is a **pre-M4.1** integrity hardening step. It is documented and frozen here; implementation belongs to a later milestone (e.g. M4.1 or a dedicated integrity milestone).

---

## 11. Non-Goals

This document does **not**:

- Implement any code, normalizer, or executor change.
- Migrate or change existing JSON schemas (e.g. execute_request, ledger_row) in this repo.
- Retroactively refactor the current runtime to use CanonicalExecutionIntent before an implementation plan exists.
- Change milestone status or roadmap tracker entries.
- Replace SandboxAction or other existing types in code—those remain until an implementation design explicitly migrates to CanonicalExecutionIntent (or a mapping from intent to SandboxAction is defined).
- Propose bypassing Plan-Gate or DeterministicGuard.
- Allow shell text to be the canonical execution truth; shell use, if any, must be represented as structured argv (e.g. `/bin/sh -c "..."`) and normalized.

---

## 12. Suggested Next Implementation Steps

A minimal, practical sequence:

1. **Design review:** Review this document with stakeholders; confirm invariant and field set.
2. **Schema draft:** Draft a schema (e.g. JSON Schema) for CanonicalExecutionIntent and optional ledger field extensions (canonical_hash, intent_id); do not apply to production schemas until approved.
3. **Normalizer prototype:** Implement CommandNormalizer (or equivalent) that produces CanonicalExecutionIntent from current execute request shape; add tests for normalization and deterministic hash.
4. **Executor integration:** Change execute path (execute_service and/or orchestrator) so that SandboxExecutor receives execution parameters derived from CanonicalExecutionIntent (or a backward-compatible adapter that carries the same identity). Ensure no layer rewrites argv/working_dir in a non-equivalent way.
5. **Ledger field extension:** Extend ledger row emission to include canonical_hash (and optionally intent_id, request_id, plan_hash) where applicable; keep append-only and backward-compatible.
6. **Replay update:** Update replay logic to use canonical_hash for matching and validation.
7. **Shadow compatibility update:** Ensure shadow baseline scenarios and comparison can use canonical_hash where relevant without crossing irreversible boundaries.

---

*End of design freeze. No implementation in this document.*
