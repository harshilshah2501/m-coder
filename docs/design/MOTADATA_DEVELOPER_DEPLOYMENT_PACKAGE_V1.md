# Motadata Developer Deployment Package v1

## Goal

Define a shareable deployment package that Motadata developers can install and use without understanding `m-coder` internals.

This is a design document only (no packaging implementation in this phase).

## Scope

- Include only developer-facing setup and usage for Ask/Debug workflows.
- Keep governance defaults intact (`PLAN_ONLY` by default for ask/debug surfaces).
- Assume API-only CLI operation for v1.
- IDE/plugin integration is optional and out of scope for v1.

## 1) Package Contents

### Core artifacts

- `mcoder-suite` wheel (CLI and ask/debug client behavior)
- Context Layer wheel/service package
- Runtime scripts required for startup/checks:
  - `runtime/scripts/governed_services.sh`
  - bootstrap/health/doctor entrypoints via `mcoder`

### Config and templates

- `.mcoder/config.yaml` template
- optional `.mcoder/context.env` template for local Context Layer service
- sample `workspace_root` + service URL values for common topologies

### Validation assets

- Ask scenario list file(s)
- Debug scenario list file(s)
- smoke commands for first-run verification

### Operational docs bundled with package

- quick-start setup
- troubleshooting matrix (timeouts, missing-file grounding, stale services)
- log/diagnostic locations

## 2) Target Topology

### Developer machine

- Motadata source checkout
- Context Layer running locally (read-only evidence export)
- `mcoder` CLI installed

### GPU / server machine

- Plan-Gate service
- vLLM explain model service
- no direct Motadata repo read requirement for v1 ask path

### Flow

- CLI -> local Context Layer (`export_evidence`)
- CLI -> remote/local Plan-Gate (`/v1/ask`)
- Plan-Gate -> vLLM only for `EXPLAIN_DEBUG` reasoning path

## 3) Setup Steps (v1)

1. Install `mcoder-suite` and Context Layer package.
2. Initialize project config:
   - `mcoder init --workspace-root <motadata-repo> --context-url <...> --plan-gate-url <...>`
3. Validate local Context Layer reachability:
   - `mcoder health`
4. Validate stack and config readiness:
   - `mcoder bootstrap`
   - `mcoder doctor`
5. Run first Ask and Debug:
   - `mcoder prompt "<question>"`
   - `mcoder debug --file <path> --query "<debug question>"`

## 4) Usage Guide (developer-facing)

### Day-to-day commands

- Ask:
  - `mcoder prompt "<question>"`
- Ask scenarios:
  - `mcoder scenario --type ask --file <ask_scenarios.txt>`
- Debug scenarios:
  - `mcoder scenario --type debug --file <debug_scenarios.txt>`
- Stack checks:
  - `mcoder health`
  - `mcoder doctor`
  - `mcoder bootstrap`

### Expected behavior

- Evidence-first grounding from Context Layer bundle
- bounded answers when snippet/context is narrow
- missing-file debug refusal when selected file is absent from retrieved evidence

## 5) Security / Governance Notes

- v1 ask path does not require repository read on GPU host.
- Default posture is `PLAN_ONLY` for ask/debug responses.
- No execution path is enabled unless explicitly using governed execute flows outside this package scope.
- Debug outputs remain evidence-bounded; no tool execution in ask/debug CLI path.

## 6) Validation Checklist (release gate)

### Service readiness

- Context Layer health check passes
- Plan-Gate health check passes
- vLLM readiness check passes

### Functional smoke

- Ask scenario suite completes successfully
- Debug scenario suite completes successfully
- First prompt/debug commands return non-error payloads

### Observability and logs

- Stack/service logs are discoverable (run directory + CLI diagnostics output)
- Failure logs include actionable hints (timeouts, path mismatch, missing-file grounding)

### Common failure modes

- **Timeouts**: increase `--timeout-sec`; warm/restart services
- **Missing-file refusal**: narrow query or ensure selected file appears in evidence
- **Stale behavior after code changes**: restart governed services
- **Workspace mismatch**: verify `.mcoder/config.yaml` `workspace_root`

## Rollout Notes

- v1 priority is reproducible setup and reliable Ask/Debug smoke behavior.
- Packaging implementation (bundling scripts/wheels into one installer) is phase 2.
- IDE-assisted workflows remain optional after API-only baseline is stable.
