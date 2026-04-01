# Stage 2 human audit checkpoint (§3.15)

**Run:** (fill) `workspace_identity_hash` from `stage2_metrics_report.md`  
**Auditor:** _________________ **Date (UTC):** _________________

Deterministic spot-checks (3 cases):

| Order | Case ID | Class | Confirm |
|-------|---------|-------|---------|
| 1 | `s2.q01` | STRONG | Top-1 file path matches real code intent in workspace. |
| 2 | `s2.q15` | NO_MATCH / refuse | Reasoning aligns with quality gate; no subtle hallucination. |
| 3 | First failed case from CSV, else `s2.q23` | failure or NO_MATCH | Same checks. |

**Sign-off:** Retrieval truth and labels are acceptable for this workspace revision.
