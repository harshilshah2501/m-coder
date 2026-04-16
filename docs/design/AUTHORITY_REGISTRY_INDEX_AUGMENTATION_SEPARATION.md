# Authority Registry vs Repo Index vs Graph/Vector Augmentation

**Document Type:** Architecture Decision Note  
**Status:** Proposed  
**Version:** 0.1  
**Date:** 2026-04-16

---

## 1) Purpose

This note separates three layers that are often conflated:

- `Authority Registry`
- `Repo Index`
- `Graph / Vector Augmentation`

They are related but not interchangeable. The design goal is to keep governance-safe trust decisions while improving retrieval quality and scale.

---

## 2) Core Distinction

### A. Authority Registry

A curated contract from:

`product concept -> trusted code authority`

It answers:

- what code is the primary owner
- what code is supporting collaborator context
- what code is an explicit distractor
- what entry points are relevant
- how fresh/validated the mapping is

It is:

- high-signal
- concept-first
- governance-facing
- auditable and versioned

It is not:

- full repo coverage
- commit history
- search index
- auto-generated canonical truth

### B. Repo Index

A broad, frequently refreshed inventory of repository structure.

It answers:

- what files exist
- what symbols/classes/methods exist
- package/module location
- local references/neighbors
- retrievable evidence candidates

It is:

- mechanical
- broad
- retrieval-facing
- repo-wide

It is not:

- final authority contract
- product concept policy

### C. Graph / Vector Augmentation

Supporting retrieval engines, not canonical governance truth.

They answer:

- graph: structural relation (caller/callee/impact paths)
- vector: semantic proximity and fuzzy concept recall

They are:

- candidate generators
- ranking enhancers
- evidence helpers

They are not:

- final owner authority
- policy contract

---

## 3) Registry vs History

### History (descriptive)

History answers:

`what changed, when, by whom`

Examples: commit log, blame, diff, PR timeline.

Useful for:

- drift detection
- freshness hints
- proposed owner changes
- audit trail

### Registry (normative)

Registry answers:

`what the system should trust now`

Used for:

- owner injection
- ranking boosts
- distractor suppression
- evidence trust shaping
- Plan-Gate posture

---

## 4) Why Registry Must Not Become Full Repo Manifest

If every file is encoded in the registry:

- signal density collapses
- review burden explodes
- governance becomes noisy
- "authority" loses meaning
- operational maintenance cost becomes excessive

Correct scaling target:

- increase concept coverage
- increase subsystem coverage
- improve owner/collaborator/distractor quality

Not:

- maximize raw file count in the registry

---

## 5) Why "Not Fully Automated" Is Still Correct

Authority is high-impact. Fully automated owner assignment is error-prone on:

- semantic responsibility shifts after refactor
- shared utility/framework glue files
- lexical false positives
- graph centrality noise
- stale semantic neighbors

Governed systems require:

`high precision + auditability`, not only high recall.

### Recommended Lifecycle (Hybrid)

1. **System proposes**
   - owner/collaborator updates
   - stale concepts
   - moved/missing paths
2. **System scores**
   - confidence
   - evidence strength
   - drift severity
3. **Human/policy gate approves**
   - especially owner swaps or high-impact concepts
4. **Registry update becomes versioned truth**

---

## 6) Layer Ownership Matrix

| Layer | Owns | Does Not Own |
|---|---|---|
| Authority Registry | Concept authority, owner hints, collaborators, distractors, freshness policy state | Full repo inventory, semantic search |
| Repo Index | Files, symbols, package topology, local references, retrieval candidates | Final authority decisions |
| Graph augmentation | Structural relation/call paths/impact routing | Canonical owner authority |
| Vector augmentation | Semantic recall and fuzzy candidate matching | Canonical owner authority |

---

## 7) End-to-End Interaction Model

1. **Repo Index** builds broad mechanical truth.
2. **Authority Registry** overlays curated product truth.
3. **Graph/Vector** improves evidence candidate quality.
4. **Retrieval/Evidence** fuses signals with explicit diagnostics.
5. **Plan-Gate/Ask** consumes evidence with trust posture (`validated`, `stale_candidate`, `unverified`, `inferred-only`).

---

## 8) Current Gaps (As Observed)

The missing pieces are not "put every file into `product_authority_registry.yaml`".  
The actual gaps are:

- narrow concept coverage relative to production breadth
- inconsistent owner signal propagation strength to ask path
- insufficient repo-wide structural locality support in some broad asks

---

## 9) Decision Thresholds and SLO Hooks (For Implementation)

These thresholds should be codified in policy/config and enforced in CI + scenario tests:

- `owner_in_top3`: required for anchored authority scenarios
- `owner_injected_lane_count >= 1`: required for owner-gated scenarios
- `anchor_hit_rate_top_k >= 0.5` for anchored asks
- `generic_infra_ratio_top_k` upper bound for broad asks (scenario-tuned)
- strict fail when registry path lint fails against target workspace

Trust posture must remain explicit in outputs:

- `validated`: execution may proceed under existing gates
- `stale_candidate`: plan-only or constrained execution
- `unverified`/`stale`: no strong ownership claims without confirmation

---

## 10) Recommended Architecture Stance

### Keep

- curated registry as governance contract
- repo index as broad inventory substrate
- deterministic retrieval + authority-aware ranking

### Add Next

- drift proposal workflow (auto-propose, not auto-commit)
- broader concept coverage expansion process
- stronger owner propagation checks on ask path
- optional graph augmentation where locality remains weak

### Avoid

- turning registry into a full manifest
- allowing graph/vector stores to silently become authority truth
- fully automated authority mutation without approval trail

---

## 11) Short/Medium/Long Horizon

### Short term

- expand registry by concept coverage (not by raw file count)
- tighten owner propagation + evidence-quality gates
- keep repo index as retrieval substrate

### Medium term

- add auto-proposed refresh pipeline with review gates
- add structural graph support if weak-locality patterns persist

### Long term

- maintain layered model:
  - curated registry
  - mechanical code index
  - graph augmentation
  - optional semantic augmentation

Registry remains the final authority contract.

---

## 12) One-Line Summary

`Registry = what to trust`  
`Index = what exists`  
`Graph/Vector = how to find better candidates`

