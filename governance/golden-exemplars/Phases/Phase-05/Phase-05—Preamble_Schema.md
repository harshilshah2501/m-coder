## Phase-05 Canonical Preamble (Identity & Scope)

This preamble is mandatory for all Phase-05 (CODE-XX) exemplars. It establishes composability, scope, and non-scope before any Five-Layer Judgment Declaration.

### Required Fields (Fixed Order)

1. **Judgment Axis**

   * The single dimension of judgment this exemplar encodes (e.g., ownership legitimacy, execution authority, safe defaults).

2. **What This Exemplar Governs**

   * The specific decision(s) this exemplar is responsible for enforcing in code.

3. **What This Exemplar Assumes Is Already Validated**

   * Preconditions that must have been satisfied by upstream exemplars or systems.
   * These are treated as invariants within this exemplar.

4. **What This Exemplar Explicitly Does NOT Decide**

   * Decisions intentionally out of scope.
   * Prevents silent scope expansion and judgment bleed.

### Non-Negotiable Rules

* The preamble MUST appear before Section A.
* The preamble MUST NOT restate Section A content.
* The preamble MUST constrain interpretation of the exemplar.
* Changes to the preamble do NOT unlock Sections A–C unless they contradict frozen judgment.

### Purpose

This preamble normalizes Phase-05 exemplars so that:

* Multiple CODE exemplars compose without contradiction
* Authority, ownership, and execution semantics are layered explicitly
* Downstream exemplars can rely on stable assumptions

This preamble is structural, not narrative.
