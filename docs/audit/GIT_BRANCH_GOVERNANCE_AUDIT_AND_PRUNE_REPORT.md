# Git Branch Governance Audit and Prune Report

## 1. Objective

- This pass classified local branches and pruned only high-confidence stale branches (merged into `main` with milestone complete on main).
- Ambiguous branches were preserved. No branch was deleted without defensible merge/supersession evidence.
- M3.12-related branches were treated conservatively and preserved per governance rules.

## 2. Scope executed

- **Branch list audited:** All in-scope local branches listed in the task (24 non-main branches). Remote-only branches were not modified; only local branches were classified and considered for prune.
- **Branches intentionally excluded:** Remote branches (e.g. `remotes/origin/*`) were not pruned; this pass is local-only. `main` was never touched.
- **Pruning mode:** Classification was completed first; then actual local deletion was performed only for branches in DELETE_MERGED with high confidence (ancestor of `main`, milestone complete per LIVE_ROADMAP_TRACKER, no ambiguity).

## 3. Classification results

| Branch | Classification | Merge/supersession basis | Short rationale | Action taken |
|--------|----------------|---------------------------|-----------------|--------------|
| Layer-2-ML-Compilation-Stage-8-Controlled-SFT | DELETE_MERGED | Ancestor of main; Layer-2 Stage-8 complete on main | Stage-8 SFT work merged; roadmap L2 COMPLETE/LOCKED | Not pruned (git -d refused: not merged to remote tracking ref) |
| cursor/greg-governance-escalation-2018 | DELETE_MERGED | Ancestor of main; M4.5 GREG complete on main | Cursor worker branch for GREG; M4.5 done | Pruned locally |
| cursor/m3.12-narrow-context-engine | KEEP_ACTIVE | Not merged into main | M3.12 next milestone; conservative preservation | Preserved |
| cursor/m4-3-collapse-vector-tracking-eb25 | DELETE_MERGED | Ancestor of main; M4.3 complete on main | M4.3 collapse tracking merged | Pruned locally |
| cursor/m4x-phase-a-verification | DELETE_MERGED | Ancestor of main; M4x merge complete | M4x verification merged | Pruned locally |
| cursor/runtime-performance-metrics-6710 | DELETE_MERGED | Ancestor of main; M4.6 complete on main | M4.6 runtime metrics merged | Pruned locally |
| feature/m3.10-m3.11-execution-isolation | DELETE_MERGED | Ancestor of main; M3.10/M3.11 complete on main | Execution isolation merged | Pruned locally |
| feature/m3.12-narrow-context-engine | KEEP_ACTIVE | Not merged into main | M3.12 next milestone; conservative preservation | Preserved |
| feature/m3.6-shadow | DELETE_MERGED | Ancestor of main; M3.6 complete on main | Shadow protocol merged | Pruned locally |
| feature/m4.1-observability-closure | DELETE_MERGED | Ancestor of main; M4.1 complete on main | M4.1 observability merged | Pruned locally |
| feature/m4.2-drift-baseline | DELETE_MERGED | Ancestor of main; M4.2 complete on main | M4.2 drift baseline merged | Pruned locally |
| feature/m4.3-collapse-tracking | DELETE_MERGED | Ancestor of main; M4.3 complete on main | M4.3 collapse tracking merged | Pruned locally |
| feature/m4.4-ledger-reconciliation | DELETE_MERGED | Ancestor of main; M4.4 complete on main | M4.4 ledger reconciliation merged | Pruned locally |
| feature/m4.5-greg-escalation | DELETE_MERGED | Ancestor of main; M4.5 complete on main | M4.5 GREG escalation merged | Pruned locally |
| feature/m4.6-runtime-metrics | DELETE_MERGED | Ancestor of main; M4.6 complete on main | M4.6 runtime metrics merged | Pruned locally |
| feature/runtime-audit-hardening | KEEP_REVIEW | Ancestor of main | Merged but audit branch; preserved for possible reference | Preserved |
| integration/layer3-next-verification | DELETE_MERGED | Ancestor of main; Layer-3 M3.0–M3.11 complete on main | Layer-3 verification merged | Pruned locally |
| integration/layer3-runtime-stack | DELETE_MERGED | Ancestor of main; Layer-3 complete on main | Layer-3 stack merged | Pruned locally |
| integration/m3.12-context-demo | KEEP_ACTIVE | Not merged into main | M3.12 cluster; conservative preservation | Preserved |
| integration/m4x-program | DELETE_MERGED | Ancestor of main; M4x merge complete (docs/reports) | M4x program merged | Pruned locally |
| layer3-plangate-decomposition | DELETE_MERGED | Ancestor of main; Plan-Gate work on main | Historical scaffolding merged | Not pruned (git -d refused: not merged to remote tracking ref) |
| layer3-plugin-runtime-bridge | DELETE_MERGED | Ancestor of main; plugin bridge on main | Historical scaffolding merged | Pruned locally |
| layer3-runtime-docs-emulator | DELETE_MERGED | Ancestor of main; runtime docs/emulator on main | Historical scaffolding merged | Pruned locally |
| main | (not classified) | N/A | Protected; never modified | No action |

## 4. Pruned branches

The following local branches were deleted (high-confidence merged, milestone complete on main):

- cursor/greg-governance-escalation-2018 — M4.5 GREG merged
- cursor/m4-3-collapse-vector-tracking-eb25 — M4.3 merged
- cursor/m4x-phase-a-verification — M4x verification merged
- cursor/runtime-performance-metrics-6710 — M4.6 merged
- feature/m3.10-m3.11-execution-isolation — M3.10/M3.11 merged
- feature/m3.6-shadow — M3.6 merged
- feature/m4.1-observability-closure — M4.1 merged
- feature/m4.2-drift-baseline — M4.2 merged
- feature/m4.3-collapse-tracking — M4.3 merged
- feature/m4.4-ledger-reconciliation — M4.4 merged
- feature/m4.5-greg-escalation — M4.5 merged
- feature/m4.6-runtime-metrics — M4.6 merged
- integration/layer3-next-verification — Layer-3 verification merged
- integration/layer3-runtime-stack — Layer-3 stack merged
- integration/m4x-program — M4x program merged
- layer3-plugin-runtime-bridge — Plugin bridge merged
- layer3-runtime-docs-emulator — Runtime docs/emulator merged

**Not pruned (git branch -d refused:** Layer-2-ML-Compilation-Stage-8-Controlled-SFT, layer3-plangate-decomposition — merged to HEAD but not to their remote-tracking refs; left for manual/remote prune.)

## 5. Preserved branches

- **KEEP_ACTIVE (M3.12 cluster):** cursor/m3.12-narrow-context-engine, feature/m3.12-narrow-context-engine, integration/m3.12-context-demo — Not merged; M3.12 is the next milestone per LIVE_ROADMAP_TRACKER. Conservative treatment per governance rules; no evidence they are obsolete or fully superseded.
- **KEEP_REVIEW:** feature/runtime-audit-hardening — Merged into main but retained for possible audit/reference; no prune to avoid losing audit trail.
- **DELETE_MERGED but not pruned (remote-tracking divergence):** Layer-2-ML-Compilation-Stage-8-Controlled-SFT, layer3-plangate-decomposition — git branch -d refused; safe to prune later with -D or after remote alignment.

## 6. M3.12 cluster treatment

- **cursor/m3.12-narrow-context-engine:** Preserved. Not an ancestor of main; M3.12 is next milestone (NOT_STARTED). No deletion.
- **feature/m3.12-narrow-context-engine:** Preserved. Not an ancestor of main; same rationale.
- **integration/m3.12-context-demo:** Preserved. Not an ancestor of main; same rationale.

There was no overwhelming evidence that these branches are obsolete or fully superseded; the roadmap explicitly states M3.12 as the next focus. Therefore all three were preserved.

## 7. Recommended branch governance policy

- **Feature branches:** Retire (delete locally, optionally remote prune) after merge to main and milestone closure confirmation.
- **Integration branches:** Retire after merge validation and milestone completion on main.
- **Cursor branches:** Retire after task closure and merge to main; treat M3.12 and similar “next milestone” clusters conservatively until milestone is closed.
- **Milestone closure:** When a milestone is marked COMPLETE/LOCKED on main, include branch retirement in the closure checklist.
- **Ambiguity:** When merge state or relevance is uncertain, classify as REVIEW_MANUAL or KEEP_REVIEW and do not delete.

## 8. Explicit non-actions

- **main:** Not modified, not deleted, not renamed.
- **History:** No rebases, squashes, resets, or force-push; no commit rewriting; no tag cleanup.
- **Repo content:** No file or directory changes except this report (`docs/audit/GIT_BRANCH_GOVERNANCE_AUDIT_AND_PRUNE_REPORT.md`).
- **Ambiguous branches:** No ambiguous branch was deleted; all M3.12 and audit-related branches were preserved.

## 9. Recommendation

- **Remote prune pass later:** Consider a separate, explicit remote prune pass after confirming with team that the listed remote branches (e.g. on origin) are safe to remove. This audit did not delete any remote refs.
- **Manual review:** Optional review of preserved branch `feature/runtime-audit-hardening` to decide whether to prune once audit references are no longer needed.
