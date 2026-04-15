# 📄 `docs/RETRIEVAL_REDESIGN_SPEC_V1.md`

---

# 1. Objective

Upgrade Layer-5 retrieval to ensure:

* High **signal-to-noise** in top-k context
* Strong **grounding** for Ask / Debug / Plan / Code
* Clear separation of:

  * retrieval signal
  * evidence quality
  * model reasoning

---

# 2. Non-Goals

* ❌ No embedding-first redesign
* ❌ No agent-based retrieval loops
* ❌ No fine-tuning dependency
* ❌ No architecture change beyond A→D pipeline
* ❌ No change to Plan-Gate / orchestration contracts

---

# 3. Retrieval Architecture (LOCKED)

```text
Stage A — Candidate Generation
Stage B — Fusion Scoring + Filtering
Stage C — Evidence Quality + Role Classification
Stage D — Context Bundle Construction
```

---

# 4. Stage A — Candidate Generation

### Sources (must remain multi-source)

* lexical match (existing)
* symbol/class match
* package/path proximity
* call graph neighbors (if available)
* active file / selection bias

### Output

```json
[
  {
    "path": "...",
    "lexical_score": ...,
    "symbol_hits": [...],
    "subsystem_tags": [...],
    "metadata": {...}
  }
]
```

No ranking finalization here.

---

# 5. Stage B — Fusion Scoring (LOCKED)

## 5.1 Precedence Order (MANDATORY)

```text
1. base lexical score
2. authority / concept boost
3. domain prior boost
4. graph / active-file boost
5. penalties (infra, distractor)
6. hard caps / normalization
7. role hint assignment (preliminary)
```

👉 No component may re-order after this stage.

---

## 5.2 Scoring Formula (INITIAL)

```text
final_score =
  + W1 * lexical_score
  + W2 * exact_symbol_match
  + W3 * class_name_match
  + W4 * package_proximity
  + W5 * authority_boost
  + W6 * domain_prior_boost
  + W7 * graph_proximity
  + W8 * active_file_overlap
  - P1 * generic_infra_penalty
  - P2 * distractor_penalty
  - P3 * weak_match_penalty
```

### Constraints

* Each boost has **max contribution cap**
* Total boost per path is capped
* Penalties can demote but not fully eliminate unless filtered later

---

## 5.3 Domain Priors (LOCKED BEHAVIOR)

* Defined in YAML (merged with existing policy/registry)
* Mapped as:

```text
query_terms → subsystem_tags → path patterns → bounded boost
```

* Must not double-count with:

  * authority boost
  * lexical subsystem inference

---

## 5.4 Intent Policy (LOCKED)

### EffectiveIntent = merge(task_type, query_intent)

Rules:

* If `task_type` present → **primary**
* query_intent → secondary bias
* conflicts logged in diagnostics

---

## 5.5 Mode-Specific Weight Adjustments

| Mode  | Bias                                   |
| ----- | -------------------------------------- |
| Ask   | symbol + package + authority           |
| Debug | graph + active file + control flow     |
| Plan  | boundaries + impacted modules          |
| Code  | exact symbol + modification-safe files |

---

## 6. Stage C — Evidence Quality + Role Classification

---

## 6.1 Role Tags (MANDATORY)

Each file must be classified:

```text
PRIMARY_OWNER_CANDIDATE
SUPPORTING_CONTEXT
DISTRACTOR_RISK
```

### Rules

* highest fused score in owner domain → PRIMARY
* graph neighbors / same subsystem → SUPPORTING
* weak lexical + infra → DISTRACTOR

---

## 6.2 Evidence Quality Levels (LOCKED)

### STRONG

* owner anchored (symbol/class/path)
* relevant snippet (definition or control flow)
* minimal distractors

### WEAK

* plausible owner/supporting
* snippet support incomplete
* some distractors present

### INSUFFICIENT

* no anchored owner
* snippet irrelevant or missing

### NO_MATCH

* no file crosses threshold

---

## 6.3 Evidence Quality Inputs

Must consider:

* fused score distribution
* symbol presence in snippet
* snippet type (definition / logic / comment)
* graph proximity (if debug)
* distractor ratio

---

## 7. Stage D — Context Bundle Construction

---

## 7.1 Bundle Structure

```json
{
  "owner_evidence": [...],
  "supporting_evidence": [...],
  "distractor_paths": [...],
  "evidence_quality": "...",
  "diagnostics": {...}
}
```

---

## 7.2 Rules

* No reordering at this stage
* Owner always included if identified
* Supporting capped by:

  * rank
  * token/byte budget
* Distractors may be excluded or flagged

---

# 8. Behavioral Contract (CRITICAL)

---

## 8.1 Ask

| Quality      | Behavior                  |
| ------------ | ------------------------- |
| STRONG       | specific grounded answers |
| WEAK         | provisional + disclaimers |
| INSUFFICIENT | ask for clarification     |
| NO_MATCH     | refuse / fallback         |

---

## 8.2 Debug

| Quality      | Behavior                     |
| ------------ | ---------------------------- |
| STRONG       | concrete failure path        |
| WEAK         | possible paths, no certainty |
| INSUFFICIENT | request file/symbol          |
| NO_MATCH     | refuse                       |

---

## 8.3 Plan / Code

* Must not produce precise changes unless STRONG
* Must include guardrails if WEAK

---

# 9. Hard Constraints (Validation Layer)

* `max_distractor_paths`
* `required_paths_any`
* `required_owner_path` (soft fail → INSUFFICIENT)
* `max_generic_infra_paths`

---

# 10. Snippet Selection Policy

Prefer:

* class definitions
* target methods
* control-flow branches

Avoid:

* comments-only
* import-only blocks
* arbitrary chunks

---

# 11. Implementation Mapping

| Stage | Location                                           |
| ----- | -------------------------------------------------- |
| A     | `retrieval/lexical.py`                             |
| B     | `retrieval/fusion.py` (new or extended rank_nudge) |
| C     | `retrieval/quality_gate.py`                        |
| D     | `evidence/builder.py`                              |

### Wiring (MANDATORY)

```text
retrieve_lexical
→ fuse_and_filter
→ authority rerank (if applicable)
→ apply constraints
→ build_evidence_bundle
```

---

# 12. Metrics (LOCKED)

### Retrieval

* owner@1
* owner@3
* distractor_count@k
* generic_infra_ratio
* anchor_hit_rate

### Debug

* selected_file_presence
* control_flow_reference_rate

### Quality

* STRONG / WEAK / INSUFFICIENT distribution

---

# 13. Acceptance Criteria

* reduction in distractor paths (>30%)
* increase in owner@1
* debug explanations reference concrete code paths
* evidence_quality improves toward STRONG for anchored queries

---

# 14. Risks

| Risk                | Mitigation               |
| ------------------- | ------------------------ |
| performance         | cache + bounded graph    |
| double counting     | strict precedence + caps |
| brittle constraints | soft fallback            |
| regression          | run PR-6 / L58 harness   |

---

# 15. Rollout Plan

1. implement fusion layer
2. integrate before evidence builder
3. enable diagnostics
4. run utility scenarios
5. tune weights
6. enforce constraints

---

# 🧠 Final note (important)

This spec enforces:

> retrieval must produce **truthful context**,
> not just plausible context.

---
