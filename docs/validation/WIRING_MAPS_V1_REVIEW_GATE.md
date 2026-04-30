# Wiring Maps V1 Review Gate

Purpose: provide a strict, repeatable review gate for wiring-map documents before they are accepted as evidence-grade artifacts.

Scope: use this gate for any wiring-map doc that claims module relationships, call paths, ownership, or system flow behavior.

---

## 1) Gate Inputs (Required)

- Candidate doc path(s): `<fill>`
- Reviewer: `<fill>`
- Review date (UTC): `<fill>`
- Source corpus used for evidence: `<fill>`
- Commit / snapshot ID reviewed: `<fill>`
- Context budget target and cap: `<fill>`

If any input is missing, set overall verdict to `FAIL (incomplete review packet)`.

---

## 2) Pass/Fail Checklist

Mark each item `PASS` or `FAIL`. Use `N/A` only when a criterion is explicitly out-of-scope and justified in findings.

### A. No inferred chains

- [ ] `PASS` / `FAIL` — Every chain step is directly supported by explicit source evidence (no speculative hops).
- [ ] `PASS` / `FAIL` — The doc does not present guessed intermediate nodes as facts.
- [ ] `PASS` / `FAIL` — Any hypothesis is clearly labeled as hypothesis and excluded from asserted chain outputs.

### B. Strict evidence tuples

- [ ] `PASS` / `FAIL` — Each asserted mapping includes a full evidence tuple: `(claim_id, source_path, symbol_or_anchor, excerpt_or_span, rationale)`.
- [ ] `PASS` / `FAIL` — Evidence tuples are traceable and reproducible by an independent reviewer.
- [ ] `PASS` / `FAIL` — Tuple fields are normalized and consistent across the document (no ad-hoc field drift).

### C. Unknown handling

- [ ] `PASS` / `FAIL` — Unknown or unresolved links are explicitly marked `UNKNOWN` (never silently filled).
- [ ] `PASS` / `FAIL` — Unknown entries include reason codes (for example: `MISSING_EVIDENCE`, `AMBIGUOUS_MATCH`, `OUT_OF_SCOPE`).
- [ ] `PASS` / `FAIL` — Unknowns are separated from confirmed mappings in structure and summary counts.

### D. Context budget guardrails

- [ ] `PASS` / `FAIL` — The doc states context budget constraints used during extraction (window, cap, truncation policy).
- [ ] `PASS` / `FAIL` — Budget overflow handling is explicit (what was dropped, how it was prioritized, and residual risk).
- [ ] `PASS` / `FAIL` — No claim relies on non-retained context outside the declared budget envelope.

### E. Testability

- [ ] `PASS` / `FAIL` — The doc defines deterministic verification steps for each high-impact chain.
- [ ] `PASS` / `FAIL` — Verification references executable checks (script/query/procedure) or exact manual reproduction instructions.
- [ ] `PASS` / `FAIL` — Expected vs actual validation signals are clearly defined (what constitutes success/failure).

### F. Acceptance criteria quality

- [ ] `PASS` / `FAIL` — Acceptance criteria are specific, measurable, and unambiguous.
- [ ] `PASS` / `FAIL` — Criteria include blocking conditions that force rejection when violated.
- [ ] `PASS` / `FAIL` — Criteria align with the declared scope and do not overclaim system certainty.

---

## 3) Findings Format (Use This Exact Structure)

Use one finding per defect. Keep language evidence-first and reproducible.

```md
### Finding <ID>: <short title>
- Severity: BLOCKER | MAJOR | MINOR
- Gate Area: A | B | C | D | E | F
- Verdict Impact: FAILS_CHECKLIST_ITEM <id>
- Claim:
  - <what the wiring map asserts>
- Evidence:
  - Tuple(s): (<claim_id>, <source_path>, <symbol_or_anchor>, <excerpt_or_span>, <rationale>)
  - Reviewer reproduction notes: <exact steps>
- Issue:
  - <what is invalid/missing and why>
- Required Fix:
  - <minimal concrete change to pass>
- Recheck Rule:
  - <what to verify after fix>
```

---

## 4) Review Output Template

```md
# Wiring Maps V1 Review Result

## Header
- Candidate doc: <path>
- Reviewer: <name>
- Date (UTC): <yyyy-mm-dd>
- Commit/snapshot: <id>

## Checklist Result
- A. No inferred chains: PASS | FAIL
- B. Strict evidence tuples: PASS | FAIL
- C. Unknown handling: PASS | FAIL
- D. Context budget guardrails: PASS | FAIL
- E. Testability: PASS | FAIL
- F. Acceptance criteria quality: PASS | FAIL

## Findings
<paste zero or more findings using the Finding format>

## Overall Verdict
- PASS (all gate areas passed, no unresolved BLOCKER/MAJOR)
- FAIL (any gate area failed or unresolved BLOCKER/MAJOR exists)

## Exit Criteria
- For PASS:
  - All checklist items PASS.
  - No unresolved findings.
- For FAIL:
  - List blocking finding IDs and required remediation owner/date.
```

---

## 5) Decision Policy (Normative)

- A single `FAIL` in any checklist item causes area-level failure.
- Any unresolved `BLOCKER` or `MAJOR` finding forces overall `FAIL`.
- `N/A` is allowed only with explicit scope justification and reviewer sign-off.
- Passing requires both:
  - all six gate areas marked `PASS`, and
  - no unresolved findings above `MINOR`.

