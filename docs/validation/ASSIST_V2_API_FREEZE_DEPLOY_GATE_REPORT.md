# Assist v2 API Freeze + Deploy Gate Report

Date: 2026-04-23  
Branch: `assist-v2-api-freeze-and-deploy-gate`

## Lane 1 — API contract freeze

Delivered:

- `docs/validation/ASSIST_V2_API_CONTRACT_FREEZE_V1.md`

Coverage:

- canonical Ask/Debug/Investigate surfaces
- required vs optional fields
- omission rules (Investigate omitted on weak Ask)
- compatibility policy (additive-only, no breaking rename/remove)
- invariant rules (`v1_evidence`, `PLAN_ONLY`, `execution=false`, fail-closed debug insufficiency)

## Lane 2 — HTTP regression/deploy gate

Delivered:

- `runtime/scripts/assist_v2_http_deploy_gate.py`
- `runtime/tests/test_assist_v2_http_deploy_gate.py`

Gate checks include:

- grounded Ask shape
- grounded Debug shape
- Investigate bridge presence (grounded Ask)
- Investigate omission (weak Ask)
- top-level `explain_debug` preserved in debug
- Ask invariants (`v1_evidence`, `PLAN_ONLY`, `execution=false`)
- missing-file debug fail-closed behavior
- graph preflight healthy requirement for deploy/staging (`COMPLETE`)

## Lane 3 — Deployment/runbook hardening

Delivered:

- `docs/guides/ASSIST_V2_BACKEND_DEPLOY_HARDENING_RUNBOOK.md`

Coverage:

- pre-deploy checklist
- startup procedure
- strict deploy gate command
- local smoke variant (`--skip-graph-preflight`)
- post-deploy acceptance criteria
- rollback notes
- artifact/log locations

## Lane 4 — Docs/tracker sync

Delivered:

- `docs/LIVE_ROADMAP_TRACKER.md` updates:
  - Assist v2 backend closure reflected
  - API freeze/deploy gate hardening tracked as active
  - plugin explicitly out of scope for this phase

## Constraint adherence

No changes were made to:

- retrieval architecture
- Stage-A behavior
- evidence quality semantics
- Ask/Debug routing semantics
- Plan-Gate governance semantics
- execution behavior
- plugin/UI code

## Lane 5 — Remote verification via WSL SSH tunnel

When Plan-Gate runs on a remote host, strict gate runs from **WSL** often use **`http://127.0.0.1:8089`** as the **local SSH tunnel bind**, not a separate on-box Plan-Gate. Evidence, commands, and conclusion for that pattern:

- `docs/validation/ASSIST_V2_DEPLOY_GATE_WSL_TUNNEL_VERIFICATION.md`

## Outcome

This phase adds deploy-grade contract hardening and regression gates without expanding product behavior scope. It is a freeze-and-verify batch, not a feature expansion batch.
