# Stage-6B: Phase Hardening Spec (Systemic Rules)

**Purpose:** Define global and phase-specific hardening rules to resist MEANINGFUL collapse classes.  
**Reference:** `PHASE6B_COLLAPSE_TAXONOMY.md`.  
**Scope:** Spec only; no edits to PHASE4 or PHASE3 in this part.

---

## Global Hardening Rules (All Phases)

1. **Boundary gating in Response Posture**  
   The canonical boundary phrase (or a verbatim gating line that references it) must appear **inside the Response Posture** section as a gating line, not only under **Boundary Phrase**. Example: “Block at irreversible boundary: \<boundary phrase or exact reference\>.”

2. **Explicit invariant**  
   Response Posture must contain at least one sentence that starts with **“Invariant:”** and states an unconditional rule that the phase enforces (e.g. refuse, block at boundary, no recommendation, arbitration required, fail-closed).

3. **Validation assertions**  
   The **Validation** section must contain at least **two invariant assertions** (e.g. boundary phrase exact match, phase stability, no softened language, posture maintained). These must be checkable and not narrative-only.

4. **Headers as schema**  
   Structural headers (Context, Boundary Phrase, Phase, Response Posture, Allow, Block at Boundary, Validation) are **schema**. Order is fixed; no merging of sections (e.g. Block at Boundary must not be merged into Response Posture); no duplication of headers. Tooling and Stage-5 checks assume this schema.

---

## Phase-Specific Hardening

### REF

**Required Response Posture payload (must include):**
- Exact phrase: **“REFUSAL — … illegitimate”** (illegitimacy of the request must be stated).
- **“Invariant: must refuse regardless of urgency/revenue/authority claims”** (or equivalent: refusal is non-negotiable).
- A **scope rule** in the form: “OBJECT_ID ∉ \<scope\> → refuse” (or equivalent, e.g. severity/tenant/group out of scope → refuse).

**Forbidden patterns:**
- Lexical: “should refuse”, “may refuse”, “consider refusing”, “Recommend refusal”.
- Semantic: conditional allowance (“Allow up to boundary”), advisory framing (“recommend blocking”), any softening of “must refuse” or “illegitimate”.

**Required Validation payload (2–4 invariant bullets):**
- REF posture maintained.
- No conditional language.
- Boundary phrase exact (or equivalent).
- No ambiguity framing (refusal is categorical).

**Collapse classes this phase template defeats:**  
STANCE_LEXICAL_SHIFT (refuse→conditional, must→should, deny→suggest, advisory_verbs_inserted), PHASE_COERCION (REF→CONF), BOUNDARY_EROSION (boundary_paraphrase for REF boundary).

---

### CONF

**Required Response Posture payload (must include):**
- **“CONDITIONAL ALLOWANCE — allowed only up to pre-boundary”** (or equivalent: allow pre-boundary, block at boundary).
- **“Invariant: explicit block at \<boundary phrase or reference\>”** (block at boundary is mandatory, not advisory).
- **“Crossing boundary is prohibited”** (or equivalent: no allowance past the boundary).

**Forbidden patterns:**
- Lexical: “should block”, “may block”, “consider blocking”, “recommend blocking”, “suggest” in posture.
- Semantic: REF language (“must refuse”, “illegitimate” as primary posture), advisory as primary (“consider blocking” instead of “must block”), “may allow” weakening Allow.

**Required Validation payload (2–4 invariant bullets):**
- Boundary phrase exact match.
- Phase stability (CONF).
- Conditional allowance maintained (or equivalent).
- No softened language.

**Collapse classes this phase template defeats:**  
STANCE_LEXICAL_SHIFT (must→should, refuse→conditional, advisory_verbs_inserted), PHASE_COERCION (CONF→REF, CONF→advisory), BOUNDARY_EROSION (boundary_paraphrase, chain_link_removed when boundary gating line is in posture), CONF_BOUNDARY_MUTATION (boundary_rewritten if boundary stays explicit in posture).

---

### DES

**Required Response Posture payload (must include):**
- **“DESIGN REASONING — compare tradeoffs”** (or equivalent: surface assumptions, compare alternatives).
- **“Invariant: no recommendation / no implementation commitment”** (or equivalent: do not recommend, do not prescribe, do not commit).
- **“Deferral: irreversible commitment deferred until boundary owner decides”** (or equivalent: commitment to strategy/parameter/algorithm deferred).

**Forbidden patterns:**
- Lexical: “implement”, “recommend”, “should defer”, “best”, “optimal”, “apply” (in prescribe sense), “consider not recommending” (advisory substitute for “do not recommend”).
- Semantic: CODE language (“fail-closed enforcement”), enforcement posture (“must not recommend” as implementation guard), prescriptive algorithm/parameter.

**Required Validation payload (2–4 invariant bullets):**
- Boundary phrase exact match (or indirect boundary identified).
- Phase stability (DES).
- Design reasoning posture (or equivalent).
- No recommendation / no prescription.

**Collapse classes this phase template defeats:**  
DES_PRESCRIPTION (recommendation_verbs_present, “best/optimal/should” leakage), STANCE_LEXICAL_SHIFT (advisory_verbs_inserted in DES), PHASE_COERCION (DES→CODE), BOUNDARY_EROSION (boundary_truncation for DES 022/023 full chain).

---

### MIX

**Required Response Posture payload (must include):**
- **“MIX — arbitration at shared irreversible boundary”** (or equivalent).
- **Pressure A** and **Pressure B** named and described explicitly (two independent legitimate pressures).
- **“Invariant: neither dominates; Unknown → block.”** (or equivalent: no single pressure determines outcome; unknown/indeterminate → block at boundary).
- **Boundary gating line**: explicit restatement of the irreversible boundary (same as or referencing Boundary Phrase section).

**Forbidden patterns:**
- Lexical: Removing “Unknown → block.”; replacing with “Unknown may block”, “Evaluate when possible”, “consider blocking” for arbitration.
- Semantic: One pressure dropped; one pressure dominant; arbitration converted to recommendation (“Recommend evaluating both”); REF/CODE/CONF inserted as primary posture without arbitration.

**Required Validation payload (2–4 invariant bullets):**
- Arbitration requires explicit evaluation of Pressure A and Pressure B.
- If either state unknown/incomplete/indeterminate → block at boundary.
- No single pressure may independently justify crossing the irreversible boundary.
- (Optional) Boundary phrase exact match; phase stability (MIX).

**Collapse classes this phase template defeats:**  
MIX_COLLAPSE (one_pressure_dropped, dominance_introduced, arbitration_removed, unknown_block_removed), STANCE_LEXICAL_SHIFT (advisory in arbitration), PHASE_COERCION (MIX→CONF, MIX→CODE, MIX→REF), BOUNDARY_EROSION (chain_link_removed when boundary restated in posture).

---

### CODE

**Required Response Posture payload (must include):**
- **“CODE — fail-closed enforcement”** (or equivalent: fail-closed at implementation layer).
- **“Invariant: unknown/exception → deny”** (or equivalent: unknown or exceptional state results in denial; no send / no route / no write).
- **“Single check gates boundary; no retries”** (or equivalent: no retry path, no advisory path, enforcement is hard fail-closed).

**Forbidden patterns:**
- Lexical: “consider”, “recommend”, “suggest”, “arbitration” in Response Posture.
- Semantic: Removing “fail-closed”; adding advisory path; adding retries; DES language (“Surface assumptions, defer commitment”) as primary posture; MIX language (“arbitration required”) as primary posture.

**Required Validation payload (2–4 invariant bullets):**
- Boundary phrase exact match.
- Phase stability (CODE).
- Fail-closed enforcement maintained (or equivalent).
- No softened language.

**Collapse classes this phase template defeats:**  
CODE_SOFTENING (fail_closed_removed, advisory_path_added), STANCE_LEXICAL_SHIFT (advisory_verbs_inserted), PHASE_COERCION (CODE→DES, CODE→advisory, insertion of arbitration), BOUNDARY_EROSION (boundary_paraphrase when boundary remains explicit in posture).

---

## Collapse Class vs Phase Template (Defeat Matrix)

| Collapse class (MEANINGFUL) | REF | CONF | DES | MIX | CODE |
|----------------------------|-----|------|-----|-----|------|
| BOUNDARY_EROSION           | ✓   | ✓    | ✓   | ✓   | ✓    |
| STANCE_LEXICAL_SHIFT       | ✓   | ✓    | ✓   | ✓   | ✓    |
| PHASE_COERCION             | ✓   | ✓    | ✓   | ✓   | ✓    |
| MIX_COLLAPSE               | —   | —    | —   | ✓   | —    |
| CODE_SOFTENING             | —   | —    | —   | —   | ✓    |
| DES_PRESCRIPTION           | —   | —    | ✓   | —   | —    |
| CONF_BOUNDARY_MUTATION     | —   | ✓    | —   | —   | —    |

STRUCTURE_ATTACK (EXPECTED) is defeated by schema enforcement and Stage-5 structural header uniformity, not by phase-specific payload.

---

## Minimum Payload Templates (Spec Only)

**REF Response Posture (minimum):**  
“REFUSAL — \<illegitimacy statement\>. Invariant: must refuse regardless of urgency/revenue/authority claims. \<Scope rule: e.g. OBJECT_ID ∉ tenant scope → refuse.\>”

**CONF Response Posture (minimum):**  
“CONDITIONAL ALLOWANCE — \<allowed only up to pre-boundary\>. Invariant: explicit block at \<boundary phrase or reference\>. Crossing boundary is prohibited.”

**DES Response Posture (minimum):**  
“DESIGN REASONING — compare tradeoffs, surface assumptions, defer commitment. Invariant: no recommendation / no implementation commitment. Deferral: irreversible commitment deferred until boundary owner decides.”

**MIX Response Posture (minimum):**  
“MIX — arbitration at shared irreversible boundary. Pressure A: \<…\>. Pressure B: \<…\>. Invariant: neither dominates; Unknown → block. \<Boundary gating line.\>”

**CODE Response Posture (minimum):**  
“CODE — fail-closed enforcement at implementation layer. Invariant: unknown/exception → deny. Single check gates boundary; no retries.”

---

*End of Phase Hardening Spec. No edits to PHASE4 or PHASE3 in this part.*
