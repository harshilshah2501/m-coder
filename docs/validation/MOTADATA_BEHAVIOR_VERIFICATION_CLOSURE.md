# Motadata AIOps behavior verification — closure summary

**Status:** **CLOSED** for the **Motadata behavior verification + Ask v1 quality** lane (2026-04-17).  
This is a **read-only** record: what is locked, what is follow-on, and where evidence lives. Do not reopen the design of **`POST /v1/ask`** evidence-quality inputs without an explicit charter; **do** re-run scenarios when stack or contracts change, and compare against the promoted baseline.

---

## What is locked (do not regress without intent)

- **Plan-Gate `POST /v1/ask` evidence quality** uses the same inputs as the layer5 export path: per-entry **`grounding_entries`** (including **`retrieval_role`**), **`effective_intent`**, and **`authority_primary_owner_file`** when calling **`assess_evidence_quality`** (implementation: `runtime/ask_service/v1_ingest.py`; landed **m-coder** `108aabb098017b8c551629c745d71f63acf7`).
- **Scenario suite** (`docs/validation/motadata_aiops_behavior_scenarios.v1.json`) with **quality policy** (`docs/validation/motadata_evidence_quality_policy.v1.json`): **`all_pass=true`** on the promoted WSL run (scenarios-only).
- **Representative outcomes** on that run:
  - **`ask_servicenow_sync_owner`:** **`evidence_quality: STRONG`** (integration owner; previously **WEAK** when `/v1/ask` omitted grounding).
  - **`ask_broad_correlation`:** **`evidence_quality: STRONG`** under the same fix.
  - **Authority Expansion Hardening v1 invariants** preserved (e.g. **`ask_api_request_routing_owner`:** no `db-files/.../highcharts.js` in export context; **`distractor_count_at_k: 0`** — see `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §6 history).
- **Anchored / debug / plan / execute / agent** scenarios in the same suite remain **passing** as recorded in the artifact (strict owner gates, EXPLAIN_DEBUG grounding, shadow plan, safe execute, no `/v0/agent`).

---

## Evidence and regression pointers

| Item | Value |
|------|--------|
| **Formal baseline record** | `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` **§5** |
| **m-coder (code fix)** | `108aabb098017b8c551629c745d71f63acf7` |
| **m-coder (docs promotion)** | `e68f3fc` (baseline policy + tracker + snapshot; message `docs(baseline): promote SERVICENOW_QUALITY_V3 + 108aabb…`) |
| **Named artifact** | `runtime/.run/motadata_behavior_validation.CANDIDATE.SERVICENOW_QUALITY_V3.motadata.json` (local / typically gitignored; regenerate with the command in §5) |
| **Workspace identity hash** (Motadata snapshot for regressions) | `b9d432fe5fe0f734e2ea6c8c4e5c2f0115502d34736c888c408b9f57a4595b86` (from scenario `actual_summary.retrieval_gates.workspace_identity_hash`) |

**Runbook:** `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`  
**Program snapshot:** `docs/PROGRAM_STATE_SNAPSHOT.md`  
**Tracker:** `docs/LIVE_ROADMAP_TRACKER.md` §5 (Current Sprint).

---

## Follow-on (explicitly non-blocking vs this closure)

- **Optional retrieval tuning** for exploratory / broad asks under **§B1 / L5-RET-VALIDATION** — must preserve **§5** invariants when run against the same scenarios.
- **Byte diff** of future candidates vs **`AUTHORITY_HARDENING_V1`** when both JSON files exist locally (historical comparator; see baseline policy §6).
- **Product surfaces** (e.g. `plan_summary.notes` everywhere) remain under their existing tracker rows — **not** part of this closure.

---

## Scope boundary

This closure is **HTTP/CLI behavior verification** for Context Layer **`export_evidence`** + Plan-Gate **`/v1/ask`** + governed routes exercised by **`runtime/scripts/motadata_behavior_verify.py`**. It does **not** replace plugin Phase-1 truth proof, IDE E2E, or unrelated production gates unless those docs say so.
