# Stage-6B: Collapse Taxonomy

**Source:** `PHASE6_MUTATION_REPORT.md`  
**Purpose:** Normalize collapse vectors into canonical classes; mark EXPECTED vs MEANINGFUL.

---

## Canonical Collapse Classes

### STRUCTURE_ATTACK

**Classification:** EXPECTED (schema tamper detection; removing/reordering headers should fail structural validation.)

| Subtype | Count | Top 5 bases affected | Representative quote (≤25 words) |
|---------|-------|----------------------|----------------------------------|
| **missing_header** | 10 | BASE-001, BASE-002, BASE-013, BASE-014, BASE-018 | "Structural header uniformity fails; invariant unenforced" |
| **reordered_sections** | 3 | BASE-001, BASE-015, BASE-021 | "Section order defines semantics; validation bypassable if reordered" |
| **merged_sections** | 1 | BASE-005 | "Boundaries merge; block conditions become narrative; bypassable" |
| **duplicated_headers** | 2 | BASE-006, BASE-024 | "Ambiguous which posture applies; semantic bypass" |

---

### BOUNDARY_EROSION

**Classification:** MEANINGFUL (semantic: boundary becomes implicit or ambiguous.)

| Subtype | Count | Top 5 bases affected | Representative quote (≤25 words) |
|---------|-------|----------------------|----------------------------------|
| **boundary_paraphrase** | 11 | BASE-001, BASE-002, BASE-003, BASE-008, BASE-011 | "Boundary implicit; chain lost" |
| **boundary_truncation** | 3 | BASE-002, BASE-022, BASE-023 | "DES 022 must include full technical chain" |
| **chain_link_removed** | 11 | BASE-001, BASE-006, BASE-007, BASE-009, BASE-010 | "Full chain required; boundary chain incomplete" |
| **irreversible_wording_softened** | 1 | (implicit in multiple) | "Boundary ambiguous" |

---

### STANCE_LEXICAL_SHIFT

**Classification:** MEANINGFUL (semantic posture drift; refusal/block becomes negotiable or advisory.)

| Subtype | Count | Top 5 bases affected | Representative quote (≤25 words) |
|---------|-------|----------------------|----------------------------------|
| **must→should** | 14 | BASE-001, BASE-002, BASE-004, BASE-006, BASE-007 | "Conditional allowance becomes advisory; CONF requires hard gating" |
| **deny→suggest** | 4 | BASE-003, BASE-008, BASE-011, BASE-021 | "Advisory; not conditional allowance" |
| **refuse→conditional** | 8 | BASE-001, BASE-003, BASE-006, BASE-008, BASE-010 | "Boundary becomes negotiable" / "Negotiable refusal" |
| **advisory_verbs_inserted** | 12 | BASE-002, BASE-004, BASE-007, BASE-009, BASE-011 | "Phase bleed" / "CODE forbids consider" |

---

### PHASE_COERCION

**Classification:** MEANINGFUL (semantic: phase posture replaced or blended.)

| Subtype | Count | Top 5 bases affected | Representative quote (≤25 words) |
|---------|-------|----------------------|----------------------------------|
| **REF→CONF** | 1 | BASE-015 | "REF refusal becomes CONF" |
| **CONF→REF** | 2 | BASE-001, BASE-002 | "CONF becomes REF framing" / "CONF conditional allowance replaced by refusal" |
| **CODE→advisory** | 2 | BASE-014, BASE-018 | "CODE enforcement becomes advisory" |
| **MIX→CONF** | 1 | BASE-024 | "MIX becomes CONF; single pressure" |
| **MIX→CODE** | 1 | BASE-013 | "MIX becomes single-axis CODE" |
| **MIX→REF** | 1 | BASE-020 | "MIX arbitration replaced by refusal" |
| **DES→CODE** | 2 | BASE-005, BASE-022 | "DES becomes CODE; design becomes implementation" |
| **CODE→DES** | 1 | BASE-025 | "CODE enforcement becomes design reasoning" |
| **CONF→advisory** | 1 | BASE-006 | "CONF conditional allowance weakened" |

---

### MIX_COLLAPSE

**Classification:** MEANINGFUL (semantic: arbitration becomes single-axis or recommendation.)

| Subtype | Count | Top 5 bases affected | Representative quote (≤25 words) |
|---------|-------|----------------------|----------------------------------|
| **one_pressure_dropped** | 3 | BASE-013, BASE-021, BASE-024 | "Single pressure; arbitration becomes single-axis" |
| **dominance_introduced** | 2 | BASE-013, BASE-024 | "One pressure dominates; arbitration collapsed" |
| **arbitration_removed** | 2 | BASE-020, BASE-021 | "Arbitration becomes recommendation; not mandatory" |
| **unknown_block_removed** | 6 | BASE-013, BASE-020, BASE-021, BASE-024 | "MIX requires exact phrase; arbitration becomes underspecified" |

---

### CODE_SOFTENING

**Classification:** MEANINGFUL (semantic: fail-closed enforcement becomes advisory or ambiguous.)

| Subtype | Count | Top 5 bases affected | Representative quote (≤25 words) |
|---------|-------|----------------------|----------------------------------|
| **fail_closed_removed** | 4 | BASE-014, BASE-018, BASE-019, BASE-025 | "CODE requires fail-closed; enforcement becomes ambiguous" |
| **advisory_path_added** | 4 | BASE-014, BASE-018, BASE-019, BASE-025 | "CODE forbids consider; advisory bleed" |

---

### DES_PRESCRIPTION

**Classification:** MEANINGFUL (semantic: design reasoning becomes prescriptive or implementation-committed.)

| Subtype | Count | Top 5 bases affected | Representative quote (≤25 words) |
|---------|-------|----------------------|----------------------------------|
| **recommendation_verbs_present** | 4 | BASE-005, BASE-012, BASE-022, BASE-023 | "DES forbids implement; becomes prescriptive" |
| **"best/optimal/should" leakage** | 3 | BASE-005, BASE-012, BASE-022, BASE-023 | "Design reasoning becomes advisory" / "Prescriptive tone" |

---

### CONF_BOUNDARY_MUTATION

**Classification:** MEANINGFUL (semantic when boundary rewritten; EXPECTED when block header removed as schema.)

| Subtype | Count | Top 5 bases affected | Representative quote (≤25 words) |
|---------|-------|----------------------|----------------------------------|
| **boundary_rewritten** | (in BOUNDARY_EROSION) | — | Covered under boundary_paraphrase / chain_link_removed |
| **block_removed** | 1 | BASE-014 | "Block conditions lost; structure incomplete" (structural → EXPECTED as missing_header) |

*Note:* CONF-specific lexical "must block → should/may block" and "allowance weakened" are under STANCE_LEXICAL_SHIFT and PHASE_COERCION.

---

## Summary: EXPECTED vs MEANINGFUL

| Canonical class | Classification | Rationale |
|-----------------|----------------|-----------|
| STRUCTURE_ATTACK | EXPECTED | Missing/reordered/merged/duplicated headers are schema violations; detection is intended. |
| BOUNDARY_EROSION | MEANINGFUL | Boundary paraphrase/truncation/chain removal is semantic weakening. |
| STANCE_LEXICAL_SHIFT | MEANINGFUL | must→should, refuse→conditional, advisory insertions are posture drift. |
| PHASE_COERCION | MEANINGFUL | Inserting another phase’s language causes phase bleed and reclassification. |
| MIX_COLLAPSE | MEANINGFUL | One pressure dropped, dominance, or removing Unknown→block collapses arbitration. |
| CODE_SOFTENING | MEANINGFUL | Removing fail-closed or adding advisory weakens enforcement semantics. |
| DES_PRESCRIPTION | MEANINGFUL | Implement/recommend/should in DES posture makes design prescriptive. |
| CONF_BOUNDARY_MUTATION | MEANINGFUL | Boundary rewrite is semantic; block_removed as header loss is STRUCTURE_ATTACK (EXPECTED). |

**Counts:**
- **EXPECTED:** 1 canonical class (STRUCTURE_ATTACK and its 4 subtypes).
- **MEANINGFUL:** 7 canonical classes (BOUNDARY_EROSION, STANCE_LEXICAL_SHIFT, PHASE_COERCION, MIX_COLLAPSE, CODE_SOFTENING, DES_PRESCRIPTION, CONF_BOUNDARY_MUTATION).
