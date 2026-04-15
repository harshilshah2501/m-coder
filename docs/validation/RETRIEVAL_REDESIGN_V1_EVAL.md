# RETRIEVAL REDESIGN V1 — EVALUATION REPORT

**Doc status:** empirical (data-backed only — no invented metrics)

**Date:** `<fill>`

**Workspace:** `<Motadata repo path / commit hash>`

**Branch:** `<branch name>`

**Evaluator:** `<name>`

---

## How to use

1. Run **Baseline** (pre–Retrieval Redesign v1) and **V1** (post-change) against the **same** Motadata checkout when possible.
2. Fill tables from **real outputs** (logs, `motadata_behavior_verify.py` reports, fusion diagnostics). If baseline is missing, note *approximate / from memory* explicitly.
3. Do not narrate success without numbers or concrete path lists.

**Helpful repo paths**

- Behavior / utility verification: `runtime/scripts/motadata_behavior_verify.py`
- Scenario JSON (examples): `docs/validation/motadata_aiops_behavior_scenarios.v1.json`, `docs/validation/motadata_developer_utility_scenarios.v1.json`
- Production verification guide: `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`

---

# 1. Objective

Evaluate impact of **Retrieval Redesign v1** on:

- retrieval signal quality
- evidence grounding
- developer usefulness (Ask / Debug / Plan)

---

# 2. Setup

## 2.1 Environment

| Item | Value |
| ---- | ----- |
| Workspace root | |
| Repo commit | |
| Index state | fresh / cached |
| Model | |
| Context layer URL | |
| Plan-Gate URL | |

## 2.2 Runs

| Run | Description |
| --- | ----------- |
| **Baseline** | Pre-redesign (or labeled pre-v1 commit) |
| **V1** | Post fusion + roles + grounding-aware quality |

---

# 3. Scenario Set

## 3.1 Utility scenarios

| ID | Type | Query | Notes |
| -- | ---- | ----- | ----- |
| U1 | Ask | | |
| U2 | Debug | | |
| U3 | Plan | | |

(Add rows as needed.)

## 3.2 Anchored evaluation set (high signal)

| ID | Query | Expected owner / class / path |
| -- | ----- | ----------------------------- |
| A1 | alert correlation engine | e.g. `AlertCorrelationEngine` |
| A2 | probe OBJECT_DOWN flow | `<fill expected>` |
| A3 | incident creation logic | `<fill expected>` |

---

# 4. Retrieval metrics (before vs after)

## 4.1 Owner accuracy

| Metric | Baseline | V1 |
| ------ | -------- | -- |
| owner@1 | | |
| owner@3 | | |

*(Define “owner” for your run: authority primary file, expected class file, or manual oracle.)*

## 4.2 Noise / distractors

| Metric | Baseline | V1 |
| ------ | -------- | -- |
| Avg distractor count (top-k) | | |
| Generic infra ratio | | |

## 4.3 Anchoring quality

| Metric | Baseline | V1 |
| ------ | -------- | -- |
| Anchor hit rate | | |
| Correct package match | | |

---

# 5. Evidence quality distribution

| Quality | Baseline | V1 |
| ------- | -------- | -- |
| STRONG | | |
| WEAK | | |
| INSUFFICIENT | | |
| NO_MATCH | | |

*(Counts or % of scenarios / queries — state which.)*

---

# 6. Ask behavior comparison

### Example: `<scenario ID>`

#### Baseline

- Top paths:
- Evidence quality:
- Answer summary:

#### V1

- Top paths:
- Evidence quality:
- Answer summary:

#### Delta

- Improvement:
- Regression:
- Notes:

(Repeat per scenario as needed.)

---

# 7. Debug quality comparison

### Example: `<scenario ID>`

| Metric | Baseline | V1 |
| ------ | -------- | -- |
| References correct file | | |
| References control flow | | |
| Concrete vs generic | | |

---

# 8. Plan / code usefulness

| Metric | Baseline | V1 |
| ------ | -------- | -- |
| Grounded file selection | | |
| Safe scope definition | | |
| Hallucination risk (qualitative) | | |

---

# 9. Utility scenario results

| Scenario | Baseline | V1 | Delta |
| -------- | -------- | -- | ----- |
| U1 | | | |
| U2 | | | |
| U3 | | | |

---

# 10. Qualitative observations

### Improvements

- 

### Regressions

- 

### Neutral

- 

---

# 11. Failure analysis

| Scenario | Failure type | Root cause (retrieval / grounding / reasoning) |
| -------- | ------------ | ----------------------------------------------- |
| | | |

---

# 12. Key insights

- 
- 
- 

---

# 13. Decision

| Question | Answer |
| -------- | ------ |
| Did retrieval improve? | YES / NO / PARTIAL |
| Is developer usefulness improved? | YES / NO / UNCLEAR |
| Ready for closure (v1)? | YES / NO |

---

# 14. Next actions

## If improvement confirmed

- Proceed to v1.1 (targeted fixes); list hypotheses:

## If not

- Identify dominant failure layer:

  - retrieval
  - grounding
  - reasoning

---

# 15. Final verdict

Retrieval redesign v1 is:

- [ ] Successful
- [ ] Partially successful
- [ ] Not effective

**Justification (evidence-only):**


---
