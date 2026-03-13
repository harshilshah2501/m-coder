## Stage-5: Variant Stability Gate (Post-6B Hardened) — Report

**Target file:** `ml/training/src/sources/Motadata/PHASE4_VARIANT_GENERATION.md`  
**Reference:** `ml/training/src/sources/Motadata/PHASE3_BASE_EXEMPLAR_MAPPING.md`  
**Mode:** Abort on first fatal. No auto-fix. No modifications to PHASE4.

---

### Check 0: Global Assertions

| Assertion | Expected | Actual | Result |
|-----------|----------|--------|--------|
| Base count | 25 (BASE-001 → BASE-025) | 25 | **PASS** |
| Variants per base | 4 (V1–V4) | 4 | **PASS** |
| Total variants | 100 | 100 | **PASS** |
| Boundary Phrase blocks per base | 4 | 4 (100 total) | **PASS** |

**Outcome:** Check 0 passed.

---

### Check 1: Boundary String Integrity

- Canonical boundary phrases from `PHASE3_BASE_EXEMPLAR_MAPPING.md` appear verbatim in each variant’s `**Boundary Phrase:**` block.
- DES BASE-022 and BASE-023: required technical chain is present in all four variants for each base:
  - `ObjectStatusCacheStore.getStore().updateItem(...)`
  - `result.put(SEVERITY, ...)`
  - `processPolicyFlap()`
  - `triggerAction(...)`
  - `EVENT_NOTIFICATION`
- No paraphrased boundary text detected; no links removed from the chain.

**Outcome:** Check 1 passed.

---

### Check 2: Phase Integrity (Response Posture Only)

Scope: text under `**Response Posture:**` only (Context / Allow / Block / Validation ignored).

- **REF** (BASE-015/016/017 variants):
  - Contains `REFUSAL —`, “must refuse”, “illegitimate”.
  - Includes scope rule (`∉ scope → refuse` or equivalent).
  - States refusal is invariant regardless of urgency/revenue/authority.
  - No conditional allowance language or softeners (`consider`, `suggest`, `could`, `instead`, `however`, `one option`).

- **CODE** (BASE-014/018/019/025 variants):
  - Contains “fail-closed” and enforcement verbs (e.g., terminate, deny, must not cross, do not invoke).
  - Invariant: unknown/exception → deny.
  - Single check gates the boundary; no retry, no advisory path.
  - No arbitration or tradeoff language.

- **MIX** (BASE-013/020/021/024 variants):
  - Opening: `MIX — arbitration`.
  - Two named pressures (Pressure A and Pressure B) for each base.
  - Explicit arbitration rule.
  - Exact phrase present: `Unknown → block.`.
  - Statement that neither pressure independently dominates.
  - Boundary explicitly referenced.

- **DES** (BASE-005/012/022/023 variants):
  - Uses “DESIGN REASONING” posture.
  - Explicit deferral; invariant: no recommendation / no commitment.
  - Tradeoff comparison language present.
  - Forbidden prescriptive verbs (`should`, `best`, `optimal`, `implement`, `apply`, prescriptive `recommend`) absent.

- **CONF** (BASE-001/002/003/004/006/007/008/009/010/011 variants):
  - Conditional allowance framing only.
  - Explicit boundary gating and clear block at irreversible boundary.
  - Invariant: crossing boundary is prohibited.
  - No relaxation of the boundary or advisory tone.

**Outcome:** Check 2 passed.

---

### Check 3: Cross-Variant Consistency

For each base (BASE-001 → BASE-025):

- All four variants (V1–V4) share the same Phase.
- All four variants contain a `**Response Posture:**` section.
- No variant is missing its phase-specific invariants within Response Posture.
- No posture drift observed across variants within the same base.

**Outcome:** Check 3 passed.

---

### Check 4: Structural Header Uniformity

Required per variant (in order):

`**Context:**`  
`**Boundary Phrase:**`  
`**Phase:**`  
`**Response Posture:**`  
`**Allow:**`  
`**Block at Boundary:**`  
`**Validation:**`

Findings:

- 100 `**Context:**` headers.
- 100 `**Boundary Phrase:**` headers.
- 100 `**Phase:**` headers.
- 100 `**Response Posture:**` headers.
- 100 `**Allow:**` headers.
- 100 `**Block at Boundary:**` / `**Block at boundary:**` headers in the expected slot.
- 100 `**Validation:**` headers.
- Header order is maintained for all 100 variants.

**Structural integrity status:** All variants have all seven headers in correct order.  
**Outcome:** Check 4 passed.

---

### Check 5: Validation Integrity

Per-variant requirements:

- Validation contains at least 3 invariant bullets or equivalent invariant lines.
- Validation mirrors the phase’s hard requirements and does not contradict `**Response Posture:**`.
- MIX: must include literal `Unknown → block.` in Validation.
- CODE: must assert fail-closed invariant.
- REF: must assert refusal invariant.
- DES: must assert deferral / non-recommendation invariant.
- CONF: must assert boundary gating invariant (crossing irreversible boundary prohibited).

Findings:

- **MIX (BASE-013/020/021/024, V1–V4; 16 variants):**
  - Each Validation section contains:
    - Arbitration evaluation invariant over Pressure A and Pressure B.
    - Unknown-state invariant at the boundary.
    - Literal bullet: `Unknown → block.` (present directly under the unknown-state line).
    - “No single pressure may independently justify crossing the irreversible boundary.”
  - Validations are phase-aligned with MIX arbitration posture and the Response Posture invariants.

- **CODE (BASE-014/018/019/025; 16 variants):**
  - Validation explicitly states fail-closed enforcement.
  - Asserts unknown/exception → deny.
  - Confirms single check gating and absence of retries/advisory paths.

- **REF (BASE-015/016/017; 12 variants):**
  - Validation asserts REFUSAL posture, illegitimacy of the out-of-scope action, and invariant refusal regardless of urgency/revenue/authority.
  - No conditional or advisory language.

- **DES (BASE-005/012/022/023; 16 variants):**
  - Validation asserts design reasoning posture and explicit deferral (no recommendation / no commitment).
  - Confirms comparative tradeoff framing without prescribing implementation.

- **CONF (remaining bases; 40 variants):**
  - Validation asserts conditional allowance with explicit boundary gating.
  - Explicitly prohibits crossing the irreversible boundary; no relaxation or advisory tone.

Across all 100 variants:

- Each Validation section has at least three invariant bullets/lines.
- All Validations are phase-aligned and consistent with their corresponding Response Posture.
- No contradictions or softening of required invariants were detected.

**Outcome:** Check 5 passed. No fatals encountered; no need to abort early.

---

### Report Summary

| Check | Description | Result |
|-------|-------------|--------|
| 0 | Global assertions (25 bases, 100 variants, 4 boundary blocks per base) | **PASS** |
| 1 | Boundary string integrity (verbatim + DES 022/023 full chain) | **PASS** |
| 2 | Phase integrity (Response Posture — REF, CODE, MIX, DES, CONF) | **PASS** |
| 3 | Cross-variant consistency | **PASS** |
| 4 | Structural header uniformity (all 7 headers) | **PASS** |
| 5 | Validation integrity (phase-aligned; MIX includes literal `Unknown → block.`) | **PASS** |

**Total bases checked:** 25  
**Total variants checked:** 100  
**First fatal:** None (no failures detected).  
**Collapse class classification:** None (no collapse observed).  
**Structural integrity status:** All structural checks passed (see Check 4).

---

STAGE-5 STABILITY GATE PASSED

