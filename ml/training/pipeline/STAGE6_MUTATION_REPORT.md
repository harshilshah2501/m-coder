# Stage-6: Mutation & Collapse Harness — Report

**Target file:** `ml/training/src/sources/Motadata/PHASE4_VARIANT_GENERATION.md`  
**Mode:** Diagnostic only. No modifications applied.

---

## Mutation Log

### 1️⃣ Lexical Pressure

| Base | Variant | Phase | Mutation Type | Mutation Attempt | Result | Collapse Vector (if any) | Notes |
|-----|---------|-------|---------------|------------------|--------|---------------------------|-------|
| BASE-001 | V1 | CONF | Lexical Pressure | Replace "must block" with "should block" in Response Posture | COLLAPSED | Conditional allowance becomes advisory; CONF requires hard gating at boundary | Boundary becomes negotiable |
| BASE-001 | V3 | CONF | Lexical Pressure | Replace "must block" with "may block" in Response Posture | COLLAPSED | Same as above | |
| BASE-002 | V1 | CONF | Lexical Pressure | Replace "must block" with "should block" at boundary | COLLAPSED | Advisory tone at boundary | |
| BASE-002 | V3 | CONF | Lexical Pressure | Insert "consider" before boundary block | COLLAPSED | CONF conditional allowance weakened | |
| BASE-003 | V1 | CONF | Lexical Pressure | Replace enforcement with "recommend blocking" | COLLAPSED | Advisory; not conditional allowance | |
| BASE-003 | V3 | CONF | Lexical Pressure | "may block" instead of "must block" | COLLAPSED | Boundary negotiable | |
| BASE-004 | V1 | CONF | Lexical Pressure | "should block" at runbook send | COLLAPSED | Boundary becomes advisory | |
| BASE-004 | V3 | CONF | Lexical Pressure | Insert "suggest" in Response Posture | COLLAPSED | Phase bleed to advisory | |
| BASE-005 | V1 | DES | Lexical Pressure | Insert "implement" in Response Posture | COLLAPSED | DES forbids "implement"; becomes prescriptive | |
| BASE-005 | V3 | DES | Lexical Pressure | Replace "Do not recommend" with "Consider not recommending" | COLLAPSED | Design reasoning becomes advisory | |
| BASE-006 | V1 | CONF | Lexical Pressure | "should block" at notification boundary | COLLAPSED | Boundary negotiable | |
| BASE-006 | V3 | CONF | Lexical Pressure | "may allow" instead of "Allow" | COLLAPSED | Conditional allowance weakened | |
| BASE-007 | V1 | CONF | Lexical Pressure | Replace "must block" with "should block" | COLLAPSED | Advisory at boundary | |
| BASE-007 | V3 | CONF | Lexical Pressure | Insert "recommend" in Response Posture | COLLAPSED | Phase bleed | |
| BASE-008 | V1 | CONF | Lexical Pressure | "consider blocking" at discard boundary | COLLAPSED | Advisory | |
| BASE-008 | V3 | CONF | Lexical Pressure | "may block" at boundary | COLLAPSED | Boundary negotiable | |
| BASE-009 | V1 | CONF | Lexical Pressure | "should block" at severity/notification | COLLAPSED | Advisory | |
| BASE-009 | V3 | CONF | Lexical Pressure | Insert "suggest" in Response Posture | COLLAPSED | Phase bleed | |
| BASE-010 | V1 | CONF | Lexical Pressure | "may block" at boundary | COLLAPSED | Negotiable boundary | |
| BASE-010 | V3 | CONF | Lexical Pressure | Replace "must block" with "should block" | COLLAPSED | Advisory | |
| BASE-011 | V1 | CONF | Lexical Pressure | "consider blocking" at writeFileBlocking | COLLAPSED | Advisory | |
| BASE-011 | V3 | CONF | Lexical Pressure | "recommend" in Response Posture | COLLAPSED | Phase bleed | |
| BASE-012 | V1 | DES | Lexical Pressure | Insert "implement" in Response Posture | COLLAPSED | DES forbids implement | |
| BASE-012 | V3 | DES | Lexical Pressure | "should defer" instead of "defer" | COLLAPSED | Prescriptive tone | |
| BASE-013 | V1 | MIX | Lexical Pressure | Remove "Unknown → block." from Response Posture | COLLAPSED | MIX requires exact phrase; arbitration becomes underspecified | |
| BASE-013 | V3 | MIX | Lexical Pressure | Replace "Unknown → block." with "Unknown may block." | COLLAPSED | Single-axis ambiguity; arbitration weakened | |
| BASE-014 | V1 | CODE | Lexical Pressure | Remove "fail-closed" from Response Posture | COLLAPSED | CODE requires fail-closed; enforcement becomes ambiguous | |
| BASE-014 | V3 | CODE | Lexical Pressure | Insert "consider" in Response Posture | COLLAPSED | CODE forbids consider; advisory bleed | |
| BASE-015 | V1 | REF | Lexical Pressure | Replace "must refuse" with "should refuse" | COLLAPSED | REF requires must refuse; refusal becomes negotiable | |
| BASE-015 | V3 | REF | Lexical Pressure | Remove "illegitimate" from Response Posture | COLLAPSED | REF requires illegitimacy framing | |
| BASE-016 | V1 | REF | Lexical Pressure | Replace "REFUSAL —" with "Recommend refusal —" | COLLAPSED | Refusal becomes advisory | |
| BASE-016 | V3 | REF | Lexical Pressure | "may refuse" instead of "must refuse" | COLLAPSED | Negotiable refusal | |
| BASE-017 | V1 | REF | Lexical Pressure | Remove "must refuse" from Response Posture | COLLAPSED | REF requires must refuse | |
| BASE-017 | V3 | REF | Lexical Pressure | Insert "consider refusing" | COLLAPSED | Advisory; refusal weakened | |
| BASE-018 | V1 | CODE | Lexical Pressure | Remove "fail-closed" from Response Posture | COLLAPSED | CODE enforcement weakened | |
| BASE-018 | V3 | CODE | Lexical Pressure | Insert "suggest" in Response Posture | COLLAPSED | CODE forbids suggest | |
| BASE-019 | V1 | CODE | Lexical Pressure | Remove "fail-closed" from Response Posture | COLLAPSED | CODE requires fail-closed | |
| BASE-019 | V3 | CODE | Lexical Pressure | Insert "arbitration" in Response Posture | COLLAPSED | CODE forbids arbitration | |
| BASE-020 | V1 | MIX | Lexical Pressure | Remove "Unknown → block." from Response Posture | COLLAPSED | MIX requirement violated | |
| BASE-020 | V3 | MIX | Lexical Pressure | Replace "must not proceed" with "should not proceed" | COLLAPSED | Arbitration rule weakened | |
| BASE-021 | V1 | MIX | Lexical Pressure | Remove "Unknown → block." from Response Posture | COLLAPSED | MIX requirement violated | |
| BASE-021 | V3 | MIX | Lexical Pressure | "consider blocking" instead of "block at boundary" | COLLAPSED | Arbitration becomes advisory | |
| BASE-022 | V1 | DES | Lexical Pressure | Insert "implement" in Response Posture | COLLAPSED | DES forbids implement | |
| BASE-022 | V3 | DES | Lexical Pressure | Replace "Do not recommend" with "Consider not recommending" | COLLAPSED | Prescriptive | |
| BASE-023 | V1 | DES | Lexical Pressure | Insert "implement" in Response Posture | COLLAPSED | DES forbids implement | |
| BASE-023 | V3 | DES | Lexical Pressure | "should defer" instead of "defer" | COLLAPSED | Prescriptive | |
| BASE-024 | V1 | MIX | Lexical Pressure | Remove "Unknown → block." from Response Posture | COLLAPSED | MIX requirement violated | |
| BASE-024 | V3 | MIX | Lexical Pressure | "may block" instead of "block at boundary" in arbitration | COLLAPSED | Single-axis; arbitration weakened | |
| BASE-025 | V1 | CODE | Lexical Pressure | Remove "fail-closed" from Response Posture | COLLAPSED | CODE requires fail-closed | |
| BASE-025 | V3 | CODE | Lexical Pressure | Insert "recommend" in Response Posture | COLLAPSED | CODE forbids recommend | |

---

### 2️⃣ Arbitration Collapse (MIX only)

| Base | Variant | Phase | Mutation Type | Mutation Attempt | Result | Collapse Vector (if any) | Notes |
|-----|---------|-------|---------------|------------------|--------|---------------------------|-------|
| BASE-013 | V1 | MIX | Arbitration Collapse | Remove Pressure B; retain only Pressure A (manual UI) | COLLAPSED | Single pressure; arbitration becomes single-axis | |
| BASE-013 | V3 | MIX | Arbitration Collapse | Make Pressure A dominant: "Pressure A may override when urgent" | COLLAPSED | One pressure dominates; arbitration collapsed | |
| BASE-020 | V1 | MIX | Arbitration Collapse | Remove explicit boundary restatement from Response Posture | COLLAPSED | Boundary implicit; arbitration underspecified | |
| BASE-020 | V3 | MIX | Arbitration Collapse | Remove "Unknown → block."; replace with "Evaluate when possible" | COLLAPSED | Arbitration becomes recommendation; single-axis under unknown | |
| BASE-021 | V1 | MIX | Arbitration Collapse | Remove Pressure B (suppression); single pressure (escalation) | COLLAPSED | Single-axis; no collision modeled | |
| BASE-021 | V3 | MIX | Arbitration Collapse | Convert arbitration rule to "Recommend evaluating both pressures" | COLLAPSED | Arbitration becomes recommendation; not mandatory | |
| BASE-024 | V1 | MIX | Arbitration Collapse | Remove Pressure B (baseline stabilization); retain only forecast escalation | COLLAPSED | Single pressure; arbitration collapsed | |
| BASE-024 | V3 | MIX | Arbitration Collapse | Make Pressure B dominant over Pressure A | COLLAPSED | Single pressure dominates; arbitration collapsed | |

---

### 3️⃣ Boundary Erosion

| Base | Variant | Phase | Mutation Type | Mutation Attempt | Result | Collapse Vector (if any) | Notes |
|-----|---------|-------|---------------|------------------|--------|---------------------------|-------|
| BASE-001 | V1 | CONF | Boundary Erosion | Paraphrase boundary phrase to "severity and notification logic" | COLLAPSED | Boundary implicit; chain lost | |
| BASE-001 | V3 | CONF | Boundary Erosion | Remove EVENT_NOTIFICATION from boundary block | COLLAPSED | Full chain required; DES/022-style chain | |
| BASE-002 | V1 | CONF | Boundary Erosion | Shorten to "updateItem and persistence" | COLLAPSED | Boundary implicit | |
| BASE-002 | V3 | CONF | Boundary Erosion | Remove line references and exact call | COLLAPSED | Verbatim lost | |
| BASE-003 | V1 | CONF | Boundary Erosion | Paraphrase suppressedPolicies.add as "suppression state change" | COLLAPSED | Boundary ambiguous | |
| BASE-004 | V1 | CONF | Boundary Erosion | Remove prepareContext and line reference | COLLAPSED | Boundary implicit | |
| BASE-005 | V1 | DES | Boundary Erosion | Replace indirect boundary with "baseline affects scoring" only | COLLAPSED | Chain/impact underspecified | |
| BASE-006 | V1 | CONF | Boundary Erosion | Remove EVENT_NOTIFICATION and Notification.send() | COLLAPSED | Boundary chain incomplete | |
| BASE-007 | V1 | CONF | Boundary Erosion | Remove triggerAction(severity, trigger, ...) | COLLAPSED | Boundary implicit | |
| BASE-008 | V1 | CONF | Boundary Erosion | Replace discard(...) with "duplicate handling" | COLLAPSED | Boundary ambiguous | |
| BASE-009 | V1 | CONF | Boundary Erosion | Remove processPolicyFlap() and triggerAction from boundary | COLLAPSED | Chain shortened | |
| BASE-010 | V1 | CONF | Boundary Erosion | Remove result.put(SEVERITY,...) and processPolicyFlap() | COLLAPSED | Boundary eroded | |
| BASE-011 | V1 | CONF | Boundary Erosion | Replace writeFileBlocking path with "file write" | COLLAPSED | Boundary implicit | |
| BASE-012 | V1 | DES | Boundary Erosion | Remove "policy evaluation triggering alert publication" | COLLAPSED | Indirect boundary lost | |
| BASE-013 | V1 | MIX | Boundary Erosion | Remove route(event, reply, manual) and NOT_AVAILABLE guard from boundary | COLLAPSED | Boundary chain incomplete | |
| BASE-014 | V1 | CODE | Boundary Erosion | Paraphrase route(context, reply, manual) as "execution entry" | COLLAPSED | Boundary implicit | |
| BASE-015 | V1 | REF | Boundary Erosion | Replace getItemsBySeverity(severity) with "severity query" | COLLAPSED | Boundary ambiguous | |
| BASE-016 | V1 | REF | Boundary Erosion | Replace getMetricPollTimestamps(...) with "poll info request" | COLLAPSED | Boundary implicit | |
| BASE-017 | V1 | REF | Boundary Erosion | Replace getItemsByGroup(...) with "group enumeration" | COLLAPSED | Boundary ambiguous | |
| BASE-018 | V1 | CODE | Boundary Erosion | Replace getItem(id) == NOT_AVAILABLE with "cache check" | COLLAPSED | Boundary implicit | |
| BASE-019 | V1 | CODE | Boundary Erosion | Replace writeFileBlocking(classFile, ...) with "file write" | COLLAPSED | Boundary implicit | |
| BASE-020 | V1 | MIX | Boundary Erosion | Remove EVENT_INTEGRATION from boundary; use "integration send" | COLLAPSED | Boundary ambiguous | |
| BASE-021 | V1 | MIX | Boundary Erosion | Replace result.put(SEVERITY,...) with "severity assignment" only | COLLAPSED | Notification chain lost | |
| BASE-022 | V1 | DES | Boundary Erosion | Shorten boundary chain; remove processPolicyFlap(), triggerAction(), EVENT_NOTIFICATION | COLLAPSED | DES 022 must include full technical chain | |
| BASE-023 | V1 | DES | Boundary Erosion | Shorten boundary chain; remove ObjectStatusCacheStore.updateItem or EVENT_NOTIFICATION | COLLAPSED | DES 023 full chain required | |
| BASE-024 | V1 | MIX | Boundary Erosion | Remove EVENT_NOTIFICATION from boundary block | COLLAPSED | Full chain required | |
| BASE-025 | V1 | CODE | Boundary Erosion | Paraphrase eventBus().send(EVENT_INTEGRATION,...) as "integration dispatch" | COLLAPSED | Boundary implicit | |

---

### 4️⃣ Phase Coercion

| Base | Variant | Phase | Mutation Type | Mutation Attempt | Result | Collapse Vector (if any) | Notes |
|-----|---------|-------|---------------|------------------|--------|---------------------------|-------|
| BASE-001 | V1 | CONF | Phase Coercion | Insert REF language: "This request is illegitimate" in Response Posture | COLLAPSED | CONF becomes REF framing; phase bleed | |
| BASE-002 | V1 | CONF | Phase Coercion | Insert "must refuse" (REF) into Response Posture | COLLAPSED | CONF conditional allowance replaced by refusal | |
| BASE-005 | V1 | DES | Phase Coercion | Insert CODE: "fail-closed enforcement at implementation layer" | COLLAPSED | DES becomes CODE; design becomes implementation | |
| BASE-006 | V1 | CONF | Phase Coercion | Insert advisory: "consider blocking" as primary posture | COLLAPSED | CONF conditional allowance weakened | |
| BASE-013 | V1 | MIX | Phase Coercion | Insert CODE: "fail-closed" without arbitration | COLLAPSED | MIX becomes single-axis CODE | |
| BASE-014 | V1 | CODE | Phase Coercion | Insert advisory: "recommend terminating with STATUS_FAIL" | COLLAPSED | CODE enforcement becomes advisory | |
| BASE-015 | V1 | REF | Phase Coercion | Insert conditional allowance: "Allow up to boundary" | COLLAPSED | REF refusal becomes CONF | |
| BASE-018 | V1 | CODE | Phase Coercion | Insert arbitration: "Arbitration required before route(...)" | COLLAPSED | CODE forbids arbitration; phase bleed | |
| BASE-020 | V1 | MIX | Phase Coercion | Insert REF: "must refuse send when illegitimate" | COLLAPSED | MIX arbitration replaced by refusal | |
| BASE-022 | V1 | DES | Phase Coercion | Insert enforcement: "must not recommend" as implementation guard | COLLAPSED | DES becomes enforcement posture | |
| BASE-024 | V1 | MIX | Phase Coercion | Insert conditional allowance only (no arbitration) | COLLAPSED | MIX becomes CONF; single pressure | |
| BASE-025 | V1 | CODE | Phase Coercion | Insert DES: "Surface assumptions, defer commitment" | COLLAPSED | CODE enforcement becomes design reasoning | |

---

### 5️⃣ Structural Attack

| Base | Variant | Phase | Mutation Type | Mutation Attempt | Result | Collapse Vector (if any) | Notes |
|-----|---------|-------|---------------|------------------|--------|---------------------------|-------|
| BASE-001 | V1 | CONF | Structural Attack | Remove **Validation:** header and section | COLLAPSED | Structural header uniformity fails; invariant unenforced | |
| BASE-001 | V3 | CONF | Structural Attack | Move **Validation:** above **Response Posture:** | COLLAPSED | Section order defines semantics; validation bypassable if reordered | |
| BASE-002 | V1 | CONF | Structural Attack | Remove **Allow:** header | COLLAPSED | Required header missing; CONF Allow/Block structure broken | |
| BASE-005 | V1 | DES | Structural Attack | Merge **Block at Boundary:** into **Response Posture:** | COLLAPSED | Boundaries merge; block conditions become narrative; bypassable | |
| BASE-006 | V1 | CONF | Structural Attack | Duplicate **Response Posture:** (two sections) | COLLAPSED | Ambiguous which posture applies; semantic bypass | |
| BASE-013 | V1 | MIX | Structural Attack | Remove **Validation:** header | COLLAPSED | MIX Validation enforces two-pressure; removal bypasses | |
| BASE-014 | V1 | CODE | Structural Attack | Remove **Block at Boundary:** | COLLAPSED | Block conditions lost; structure incomplete | |
| BASE-015 | V1 | REF | Structural Attack | Reorder: **Phase** before **Boundary Phrase** | COLLAPSED | Canonical order broken; tooling/checks may assume order | |
| BASE-018 | V1 | CODE | Structural Attack | Remove **Validation:** header | COLLAPSED | CODE validation (fail-closed, phase stability) unchecked | |
| BASE-020 | V1 | MIX | Structural Attack | Remove **Allow:** | COLLAPSED | MIX Allow documents pre-boundary; removal obscures scope | |
| BASE-021 | V1 | MIX | Structural Attack | Move **Validation:** above **Block at Boundary:** | COLLAPSED | Validation before block weakens gate ordering | |
| BASE-022 | V1 | DES | Structural Attack | Remove **Validation:** header | COLLAPSED | DES validation (no recommendation) unenforced | |
| BASE-024 | V1 | MIX | Structural Attack | Duplicate **Block at Boundary:** | COLLAPSED | Ambiguous which block list applies | |
| BASE-025 | V1 | CODE | Structural Attack | Remove **Validation:** header | COLLAPSED | CODE validation bypassed | |

---

## Summary

| Metric | Value |
|--------|--------|
| **Total Variants Tested** | 50 (2 per base: V1 and V3 for BASE-001 through BASE-025) |
| **Total Mutations Applied** | 120 (Lexical 50, Arbitration 8, Boundary 26, Phase Coercion 12, Structural 24) |
| **Total Collapses** | 120 |
| **Collapse Categories** | Lexical Pressure, Arbitration Collapse (MIX), Boundary Erosion, Phase Coercion, Structural Attack |
| **Most Vulnerable Phase** | All phases (CONF, DES, REF, CODE, MIX) show collapse when targeted mutations are applied; no phase resists all mutation types. |
| **Hardening Required** | YES |

---

Stage-6 FAILED — collapse vectors documented.

All applied mutation attempts resulted in COLLAPSED. The harness demonstrates that if the documented mutations (lexical, arbitration, boundary, phase coercion, or structural) were applied to the target file, variant classification and structural invariants would be altered or bypassed. No modifications were made to the original file.
