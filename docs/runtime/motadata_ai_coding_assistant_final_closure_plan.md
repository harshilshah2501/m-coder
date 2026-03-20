# Motadata AI Coding Assistant — Final Closure Plan

## Current Status

You are at ~85–90% completion.

All core systems are built and working in isolation:
- Runtime (Plan-Gate, Sandbox, Ledger) ✅
- Observation / Explainability (Track-C) ✅
- Model serving via GPU (vLLM + adapter) ✅
- JetBrains Plugin (installed, actions visible) ✅

The remaining work is **integration closure + demo hardening**.

---

## Definition of Full Closure

Closure is achieved only when ALL of the following are true:

1. Plugin loads in IntelliJ
2. Plugin reaches governed runtime
3. Runtime reaches reasoner (vLLM)
4. Selected AIOps code produces grounded explanation
5. Ask responses show grounded file evidence (relevant files + reasons), not connectivity-only success
6. One golden demo path works repeatedly
7. Audit proof (ledger / canonical_hash) can be shown
8. Codebase + branches + docs are clean and stable

---

# Phase 1 — Runtime Connectivity Closure (BLOCKER)

## Objective
Ensure IntelliJ plugin communicates with the **correct governed runtime service**.

## Steps

### 1. Verify runtime endpoints (from Windows)
- POST `/v0/ask`
- POST `/v0/execute`

Outcome:
- If JSON response → correct runtime
- If 404 → wrong service bound to 8089

### 2. Fix endpoint mismatch
One of:
- Correct SSH/port forwarding
- Point plugin to correct runtime port
- Ensure runtime is actually running on expected port

### 3. Validate plugin actions
- "Ask Motadata AI"
- "Submit to Runtime"

Success criteria:
- No "Runtime service not available"
- Responses come from real runtime

---

# Phase 2 — Golden Demo Validation

## Objective
Prove system works on **real Motadata AIOps code**.

## Steps

### 4. Select one code example
Criteria:
- Real AIOps logic
- 40–120 LOC
- Contains potential failure point

Examples:
- Alert correlation
- Topology resolution
- Incident enrichment

### 5. Run explain/debug
Prompt:
> What is this code doing and where is the most likely failure risk?

Success criteria:
- References real code symbols
- Explains actual logic
- Identifies concrete failure risk
- Evidence grounded in code

### 6. Run follow-up (only if above is solid)
Prompt:
> What is the smallest safe fix?

Success criteria:
- Local, minimal fix
- No hallucinated architecture
- No generic answer

---

# Phase 3 — Demo Hardening

## Objective
Make demo stable and repeatable.

## Steps

### 7. Repeat demo 5–10 times
- Same file
- Same prompt
- Same flow

Success criteria:
- Stable output
- No runtime failures
- Predictable latency

### 8. Lock environment
Freeze:
- Ports (8000, 8089)
- Model name
- Adapter checkpoint
- Runtime env vars
- Plugin version
- IntelliJ version

### 9. Prepare audit fallback
Have ready:
- request_id
- canonical_hash
- one trace query

Used only if asked during demo.

---

# Phase 4 — Codebase & Project Closure

## Objective
Finalize system and stop development drift.

## Steps

### 10. Merge plugin demo branch → main
Conditions:
- Plugin fully working
- Runtime connectivity validated
- Golden demo confirmed

### 11. Update tracker/docs
Include:
- Explain/debug path completed
- Real reasoning integrated
- Demo validated

### 12. Branch cleanup
- Delete temporary demo branches
- Keep only active development branches

### 13. Freeze scope
DO NOT add:
- New features
- More actions
- Autonomous coding flows

Closure = stabilization, not expansion.

---

# Phase X — Workspace Intelligence Integration

## Objective
Move repo-aware context retrieval to workspace-local authority while keeping reasoning/governance centralized.

## Steps

### X1. Introduce Context Layer authority near workspace
- Establish Workspace Intelligence Context Layer in WSL as retrieval/indexing source of truth.
- Keep plugin as interaction/orchestration client and Plan-Gate as governance authority.

### X2. Refactor Ask flow to evidence-driven contract
- Ask path should send structured context/evidence bundle upstream.
- Avoid relying on remote runtime filesystem assumptions for repo-aware grounding.

### X3. Enable Plan-Gate evidence bundle ingestion
- Plan-Gate consumes structured evidence (files/snippets/reasons/selectors/revision) for ask/plan reasoning.
- Preserve bounded PLAN ONLY semantics and auditability.

### X4. Deprecate direct `repo_root` dependency for final mode
- Keep `repo_root` compatibility for demo mode during transition.
- Define deprecation path where workspace-local retrieval is default in production mode.

Success criteria:
- Ask produces grounded evidence from workspace-local context.
- Plan-Gate reasoning is evidence-ingested and consistent with retrieved files.
- Demo mode compatibility remains available as transitional path only.

---

# Final Closure Checklist

All must be TRUE:

- [ ] IntelliJ → runtime (8089) works from Windows
- [ ] Ask action returns real explanation
- [ ] Submit action works without error
- [ ] One real AIOps example validated
- [ ] Follow-up answer is acceptable
- [ ] Demo repeatable (5–10 runs)
- [ ] Environment locked
- [ ] Branch merged to main
- [ ] Docs updated

---

# Effort Estimate

## Best Case
- 1 session → fix runtime endpoint
- 1 session → validate + rehearse demo

## Realistic
- 2–3 focused sessions total

---

# Immediate Next Action

Resolve exactly what service is bound to:

127.0.0.1:8089 (from Windows)

and ensure it is the governed runtime service used by the plugin.

This is the final integration knot.

Once solved → proceed directly to Golden Demo Validation.

