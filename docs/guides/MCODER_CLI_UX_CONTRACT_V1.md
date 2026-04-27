# MCODER CLI UX CONTRACT V1

## Status

Frozen UX contract for the first `mcoder` CLI surface.

This document is specification-only.

- No CLI implementation is introduced here.
- No runtime behavior changes are introduced here.
- No Stage 3 execution, patch application, retry loop, or mutation behavior is enabled.

## Core Principle

`mcoder` is a contract-aware API client, not a shell wrapper.

The CLI must:

- load configuration deterministically
- validate required inputs before dispatch
- normalize workspace/file paths
- call only approved API surfaces
- surface governance posture and evidence quality
- preserve API-only topology
- preserve model outputs without semantic enrichment beyond formatting
- never expose direct vLLM access
- never provide mutation or execution commands in V1

## Architecture Boundary

```text
Developer IDE / terminal
  -> mcoder CLI
  -> local Context Layer API
  -> evidence bundle
  -> Plan-Gate API
  -> vLLM behind Plan-Gate only
```

Rules:

- IDEs call `mcoder` or local APIs only.
- IDEs never call vLLM.
- IDEs never send raw repository content to GPU.
- Plan-Gate remains the only model gateway.
- Context Layer remains workspace-local.

## Command Surface V1

### Core Developer Commands

```bash
mcoder ask "How does alert correlation work?"
mcoder ask "How does alert correlation work?" --strict
mcoder debug --file src/.../X.java --symbol methodName
mcoder inspect src/.../X.java:methodName
mcoder plan "Refactor this handler safely"
mcoder propose "Suggest bounded patch for this issue"
```

### Setup and Health Commands

```bash
mcoder configure --workspace-root /home/user/Projects/Motadata --plan-gate-url http://gpu-host:8089
mcoder doctor
mcoder start-context
mcoder stop-context
mcoder status
mcoder verify
mcoder version
```

## Command Semantics

### `mcoder ask`

Purpose: governed question answering through local evidence and Plan-Gate.

Required behavior:

- export evidence from local Context Layer
- call Plan-Gate `/v1/ask`
- display answer, governance posture, execution flag, and evidence quality
- default to human-readable output
- support machine-readable JSON output via `--json`
- support `--strict`

Strict mode:

- fail if `evidence_quality` is not `STRONG`
- fail on `NO_MATCH`, `INSUFFICIENT`, or equivalent insufficient-evidence status
- return an explicit error response instead of weakening the answer

### `mcoder debug`

Purpose: explain/debug a selected file or symbol using grounded evidence.

Required behavior:

- require `--file`
- optionally accept `--symbol`
- normalize file path relative to workspace when possible
- send debug intent through approved Ask/Debug path
- never execute code or tests

### `mcoder inspect`

Purpose: read/reason-only inspection of a file/symbol target.

Example:

```bash
mcoder inspect src/.../X.java:methodName
```

Required output:

- whether the file is recognized
- whether symbol/method grounding is available
- evidence quality
- available surfaces:
  - `ask`
  - `debug`
  - `investigate`
  - `propose` only when enough plan/reasoning chain exists

`inspect` must not dump raw file content by default.

Determinism rule:

`inspect` must not depend on model response. It should rely only on Context Layer output, workspace metadata, and deterministic grounding signals.

### `mcoder plan`

Purpose: produce governed planning output only.

Required behavior:

- surface plan summary and constraints
- include governance posture and evidence quality
- never execute the plan
- never mutate files

### `mcoder propose`

Purpose: surface bounded proposal metadata only.

Required behavior:

- return `patch_proposal.v1` metadata only
- preserve `human_review_required=true`
- surface bounded scope, risks, test plan requirements, and rollback requirements
- never apply changes
- never execute validation commands

V1 restriction:

`mcoder propose` must not output raw patch diffs unless a future `patch_text.v1` contract is frozen.

## Forbidden Commands V1

These commands must not exist in V1:

```bash
mcoder execute
mcoder apply
mcoder run
mcoder retry
```

Forbidden aliases:

```bash
mcoder fix
mcoder auto
mcoder agent
```

Rationale: V1 is a governed thinking/proposal interface, not an acting system.

## Configuration Contract

Default config path:

```text
~/.mcoder/config.yaml
```

Example:

```yaml
workspace_root: /home/user/Projects/Motadata
context_url: http://127.0.0.1:8091
plan_gate_url: http://gpu-host:8089
mode: api_only
output: human
```

Precedence:

1. CLI flags
2. environment variables
3. `~/.mcoder/config.yaml`
4. built-in defaults

Required validation:

- `workspace_root` exists and is a directory
- `context_url` is reachable for Context Layer commands
- `plan_gate_url` is reachable for Plan-Gate commands
- `mode` must be `api_only` in V1

## Output Contract

Default human output should be concise and stable:

```text
request_id: ...
trace_id: ...
posture: PLAN_ONLY
execution: false
mutation: false
evidence_quality: STRONG
ask_path: v1_evidence

Answer:
...

Next:
...
```

Machine output uses `--json`:

```json
{
  "request_id": "...",
  "trace_id": "...",
  "command": "ask",
  "status": "ok",
  "governance_posture": "PLAN_ONLY",
  "execution": false,
  "mutation": false,
  "evidence_quality": "STRONG",
  "answer": "...",
  "diagnostics": {
    "ask_path": "v1_evidence",
    "context_url": "http://127.0.0.1:8091",
    "plan_gate_url": "http://gpu-host:8089",
    "retry_attempts": 0
  }
}
```

Every command must answer:

1. Did it run through the governed path?
2. What evidence quality did it have?
3. Was execution/mutation attempted?

For V1, execution and mutation must always be false.

If Plan-Gate or Context Layer returns `trace_id`, CLI JSON output must surface it for distributed log correlation.

The CLI must not transform, summarize, expand, or enrich model output beyond stable formatting and field selection. It is a governed client, not a second reasoning layer.

## Error Contract

Errors must be explicit and scriptable.

```json
{
  "status": "error",
  "error_class": "context_layer_unreachable",
  "message": "Context Layer is not reachable at http://127.0.0.1:8091",
  "next_action": "Run: mcoder start-context"
}
```

Required error classes:

- `config_missing`
- `workspace_not_found`
- `context_layer_unreachable`
- `plan_gate_unreachable`
- `evidence_export_failed`
- `request_validation_failed`
- `policy_blocked`
- `unsupported_command`

## IDE Integration Contract

V1 IDE integration should be command-based:

- VSCode/Cursor: terminal tasks invoking `mcoder`
- IntelliJ: External Tools invoking `mcoder` through WSL when needed
- no first-party plugin required for V1

IDE integrations must not:

- call vLLM directly
- bypass Plan-Gate
- send raw repo content to GPU
- introduce mutation or execution affordances

## Verification Commands

`mcoder doctor` should verify local configuration and service reachability.

Expected checks:

- config file present or valid defaults available
- workspace root exists
- Context Layer reachable
- Plan-Gate reachable
- API-only mode active

`mcoder verify` should run a broader governed smoke check.

Expected output shape:

```text
Context Layer: OK
Plan-Gate: OK
vLLM reachable through Plan-Gate: OK
Graph preflight: COMPLETE
Assist v2 API gate: PASS
Plan/Code gate: PASS
```

## Safety Rules

- No direct model access from CLI.
- No raw repository upload to GPU.
- No execution commands in V1.
- No patch application commands in V1.
- No hidden retries.
- Default V1 behavior is no retries.
- If a future retry occurs, it must be surfaced explicitly in human output and JSON (`retry_attempts`, retry reason, and final outcome).
- No mutation under `ask`, `debug`, `inspect`, `plan`, or `propose`.
- `propose` is metadata-only until a future patch-text contract is frozen.

## Rollout Recommendation

1. Implement repo-local `scripts/mcoder`.
2. Publish `MCODER_API_ONLY_DEVELOPER_SETUP.md`.
3. Run internal dry run with 2-3 developers.
4. Observe friction and stabilize command semantics.
5. Promote to installable CLI only after V1 behavior is stable.
