# CI Execution Model

Concise reference for what CI is allowed to do in this repository. Governed execution is for the IDE/runtime path only; CI must not invoke it for user-supplied commands.

---

## 1. CI scope

CI is limited to:

- **Tests** — unit, integration, or structural tests (e.g. pytest, script-based checks).
- **Builds** — compilation, packaging, artifact generation.
- **Structural checks** — invariants on repo layout, boundaries, and config (e.g. `scripts/ci/` guards).

CI must not perform user-facing execution, run arbitrary user commands through the runtime, or act as a substitute for the governed execution path.

---

## 2. No governed execution for user-supplied commands

CI **must not** call the governed runtime execution path for user-supplied or externally supplied commands. That path is:

- Plugin → `/v0/execute` → Plan-Gate → ledger → SandboxExecutor (if safe_execute) → response.

CI may run **fixed** test commands (e.g. `pytest`, `python -m scripts.ci.check_structure`) that are defined in CI config or scripts, not passed through as user input. CI must not invoke the execute service or sandbox with commands that come from PR content, branch content, or any untrusted input as the execution payload.

---

## 3. No bypass of Plan-Gate or SandboxExecutor

CI must not:

- Bypass Plan-Gate or SandboxExecutor.
- Call `/v0/execute` (or equivalent) to run user-supplied commands.
- Use runtime execution as a generic “run this command” step in the pipeline.

Governed execution remains the sole path for running user-requested actions; CI stays outside that path.

---

## 4. In-repo CI and external platforms

At present there are **no in-repo CI workflow definitions** (e.g. no `.github/workflows/` in the tree). CI may be run externally or locally. This document defines the **expected CI execution model** regardless of where CI runs: any CI (in-repo or external) must follow the scope and prohibitions above. When adding in-repo workflows (e.g. GitHub Actions), keep them to tests, builds, and structural checks; do not add steps that invoke governed execution for user-supplied commands.

---

## Summary

| Allowed | Not allowed |
|--------|-------------|
| Tests, builds, structural checks | Invoking governed execution for user-supplied commands |
| Fixed test/build commands in CI config | Bypassing Plan-Gate or SandboxExecutor |
| Scripts that only inspect repo structure | Using `/v0/execute` or sandbox as a generic command runner in CI |
