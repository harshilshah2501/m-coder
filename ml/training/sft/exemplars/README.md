# Golden SFT Exemplars

This directory contains the **canonical golden exemplars** used for
Supervised Fine-Tuning (SFT) of the Motadata engineering assistant.

These exemplars encode **senior-engineer judgment**, not product workflows
or happy-path automation.

They are written manually, validated rigorously, and locked before any
variant generation or model training.

---

## What These Exemplars Are

Golden exemplars are:

- High-signal, low-volume training artifacts
- Grounded in real or highly plausible production scenarios
- Explicit about uncertainty, constraints, and risk
- Designed to survive adversarial mutation (D.N.A-tested)
- Category-balanced across architectural stress surfaces

They teach the model **how to think**, not just what to answer.

---

## What These Exemplars Are NOT

Golden exemplars are **not**:

- Product documentation
- UI walkthroughs or API references
- Runbooks or automation scripts
- Feature demos
- Exhaustive coverage of all scenarios

Product specificity is intentionally limited at this stage.
It is introduced later via variants and RAG.

---

## Authoring Framework

All exemplars follow the **B.R.A.I.N → D.N.A** framework:

### B.R.A.I.N (Creation Discipline)
- **B**oundary First (constraints)
- **R**eality-Anchored situation
- **A**mbiguity Injection
- **I**ntent Resolution
- **N**arrative Reasoning

### D.N.A (Validation Discipline)
- **D**ecomposition (atomic decision blocks)
- **N**egative Capability (safe stopping)
- **A**dversarial Swap (mutation survival)

No exemplar is accepted without passing **all D.N.A checks**.

---

## Directory Structure

training/sft/golden-exemplars/
├── RCA/
├── Anomaly/
├── Refusal/
├── Config/
├── Design/
└── Mixed/


Each category contains:
- Individual exemplar files (`RCA-01.md`, `ANOM-01.md`, etc.)
- A category-specific `README.md` explaining intent and review lens

---

## Locking Rules

An exemplar is considered **LOCKED** only when:

- All 6 essential fields are explicit
- Reviewer checklist passes
- At least one adversarial swap has been mentally tested
- The exemplar constrains future model behavior (not just agrees)

Locked exemplars must **not be edited casually**.
Revisions require re-running D.N.A.

---

## Scaling Strategy (Later Phase)

This directory intentionally contains **only ~30 files**.

Scale comes from:
- controlled variants
- re-grounding
- paraphrasing
- adversarial mutations

Not from adding more base exemplars.

---

## Current Status

- RCA-01 ✅ Locked
- RCA-02 ✅ Locked
- REF-01 ✅ Locked
- Remaining exemplars ⏳ In progress

Refer to `sft_golden_exemplars_30_item_authoring_todo.md` for progress tracking.

---

## Reviewer Reminder

> Review these exemplars as if you are reviewing a colleague’s **judgment**,  
> not their **code**.

If you would trust the thinking at 2 a.m., approve it.
If not, explain why.

---

## File Conventions

- Filenames must be stable (`RCA-02.md`)
- Do not rename locked exemplars
- Variants must live outside this directory
- Each exemplar must declare:
  - Situation Type
  - Signal Ambiguity
  - Constraints
  - Intent
  - Reasoning Path
  - Response Posture

No partial drafts in this directory.
Use temp files elsewhere.
