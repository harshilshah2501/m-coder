# Verification / demo / testing doc allowlist (frozen)

**Purpose:** Scope boundary for consolidation edits. **Only** the paths listed below may be changed when deduplicating manual HTTP flows, verifier commands, or cross-links between testing/demo/verification guides.

**Do not edit** canonical or authority documents (`docs/LIVE_ROADMAP_TRACKER.md`, `docs/SYSTEM_TRUTH.md`, `docs/DOC_AUDIT_LEDGER.md`, layer specs, `docs/NAVIGATION_HUB.md`, etc.) as part of that work unless a separate program decision expands scope.

## Allowlisted files

| Path | Role |
|------|------|
| [MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md](MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md) | Primary spine: setup, §6 manual options, **§6.3.1 canonical `run_v1_ask`** |
| [../../MCODER_USER_SCENARIOS_GUIDE.md](../../MCODER_USER_SCENARIOS_GUIDE.md) | Scenario semantics, links to simple path |
| [../../MOTADATA_SIMPLE_PATH.md](../../MOTADATA_SIMPLE_PATH.md) | Thin router |
| [../demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md](../demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md) | Verifier stdout / JSON |
| [../MOTADATA_DEMOBOOK.md](../MOTADATA_DEMOBOOK.md) | Capability demobook |
| [../MOTADATA_DEMO_SETUP_RUNBOOK.md](../MOTADATA_DEMO_SETUP_RUNBOOK.md) | Demo setup order |
| [../MOTADATA_DEMO_SCENARIOS.md](../MOTADATA_DEMO_SCENARIOS.md) | Demo success criteria |
| [../DEBUG_PATH_VALIDATION_RUNBOOK.md](../DEBUG_PATH_VALIDATION_RUNBOOK.md) | Debug path capture (defers duplicate bash to production guide) |
| [../Backend Production Validation Sheet.md](../Backend%20Production%20Validation%20Sheet.md) | Backend validation sheet |
| [MOTADATA_DEVELOPER_UTILITY_VALIDATION.md](MOTADATA_DEVELOPER_UTILITY_VALIDATION.md) | Utility validation (optional cross-links) |

**Schema/data (not prose merges):** `docs/validation/*.json` scenario packs — edit only when changing contracts, not as part of narrative consolidation.

Last updated: consolidation pass (verification/demo guides only).
