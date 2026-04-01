# PR-6 — True-Positive Debug Validation + Minimal Semantic Retrieval Lift Plan

## 1. Executive summary

PR-6 exists to close **Action Item 6B**: debug-path semantic adequacy for **real true-positive Motadata AIOps debug cases**.

The current system is no longer broken at the mechanism level. The governed path is in place: Layer-5 evidence-first Ask is wired, `/v1/ask` is validated, the plugin/runtime split is defined, and Plan-Gate + vLLM can produce weak-evidence-truthful debug outputs. What is still unproven is the part that actually matters in production: whether the system can retrieve the **right AIOps implementation file(s)** when the query references a real class, function, or symbol that truly exists in the repo.

So PR-6 is intentionally narrow:

- prove a **small true-positive debug set** against real AIOps code
- add only the **minimum deterministic retrieval lift** needed to make those cases work
- keep the change in **Layer-5 retrieval / evidence packaging**, not a broad architecture rewrite
- validate with **request-level pass/fail rules**, not vibes, screenshots, or one lucky run

This is **not** a semantic-search redesign, **not** embeddings-first retrieval, **not** plugin work, and **not** execute-path validation. Execute-path validation remains later under Action Item 7.

The recommended first slice is:

1. add **symbol-first exact lookup + identifier normalization + path/package priors**
2. define **5–8 true-positive debug cases** from real AIOps code
3. run a deterministic validation harness where each case asserts **top-k retrieval**, **evidence quality posture**, and **debug output grounding**
4. accept PR-6 only if true-positive debug retrieval is no longer semantically blind

---

## 2. Problem statement

The current system is **mechanism-correct but semantically weak**.

Mechanism-correct means the governed path is behaving as intended:

- evidence-first Ask path exists and is validated
- Plan-Gate receives structured evidence rather than relying on hidden repo access
- debug/explain can invoke vLLM
- weak or empty evidence can produce truthful insufficiency instead of hallucinated certainty

That closes “does the pipe work?” It does **not** close “does the pipe find the right code?”

The active production blocker is that retrieval remains **lexical-first and noisy**, and the current closure documents explicitly say evidence bundles are often dominated by tests, logs, vendor assets, and non-core files while `src/main/java/com/mindarray/aiops/*` is underrepresented. That makes the system capable of honest failure, but not yet capable of **reliable true-positive debug grounding**.

Why Capture-5 does not close adequacy:

- Capture-5 validated a **weak/no-match** scenario
- it proved the system can say “I do not have enough grounded evidence”
- it did **not** prove the system can find the correct file when the symbol is real and present
- therefore it validated **debug-path integrity**, not **debug-path semantic adequacy**

True-positive validation is mandatory because production debug usefulness depends on four things happening together:

1. the right symbol must be recognized as a symbol-like intent
2. the correct implementation file must rank high
3. evidence must be code-dominant and not drowned by non-code artifacts
4. the debug answer must stay grounded in retrieved evidence

Until that is proven on real AIOps symbols, Action Item 6B remains open.

---

## 3. Why Action Item 6B remains open

Action Item 6B remains open for one simple reason:

> the system has proven honest weakness, but not real debug strength.

What is already closed:

- retrieval bias work (PR-1 through PR-5) established deterministic controls, evidence gating, calibration, and weak/no-match honesty
- debug-path validation established that explain/debug uses the evidence-first governed path rather than hidden repo access
- runtime and Plan-Gate architecture are already in place, so this is not a governance/runtime-gap problem

What is still missing:

- a **true-positive debug corpus** tied to real AIOps implementation symbols
- deterministic retrieval behavior that makes those symbols surface in the top retrieval set
- pass/fail evidence showing that debug output is grounded when the answer actually exists

Current closure documents already identify retrieval as a non-negotiable blocker:

- evidence must be dominated by AIOps implementation code
- tests/logs/vendor assets must not dominate
- weak evidence must be explicitly surfaced
- path priors and symbol-aware normalization are still needed

That means 6B is not a theoretical gap. It is the next concrete blocker between “good demo plumbing” and “production-credible repo-aware debugging.”

---

## 4. Current failure pattern from debug validation

The failure pattern is now clear and should be documented precisely.

### 4.1 What worked

The following behaviors are already validated and should be treated as preserved invariants:

- no hidden repo access
- evidence-first `/v1/ask` path is contract-correct
- vLLM can be invoked for debug/explain
- weak evidence produces truthful limitation language
- debug path does not fake confidence when grounding is poor

### 4.2 What failed

The unresolved defect is **semantic blindness on real code lookup**.

Typical pattern:

1. user asks a debug question about a symbol/class/function
2. retrieval behaves mostly lexically
3. noisy artifacts or broad token matches outrank the actual implementation file
4. evidence quality degrades to weak / code-intent unresolved / no-symbol-match
5. debug output becomes truthful-but-unhelpful instead of grounded-and-useful

### 4.3 Structural causes of failure

The current closure docs already point to the likely root causes:

- implementation files under `src/main/java/com/mindarray/aiops/*` are underweighted
- tests/logs/vendor assets still dominate top-k in many cases
- identifier normalization is not strong enough for CamelCase / symbol-style queries
- retrieval has insufficient bias toward same file / same package / same module when debugging
- symbol-like debug requests are not yet routed through a deterministic **symbol-first** lookup lane before generic lexical scoring

### 4.4 What this means operationally

The system today is better described as:

- **honest under weak evidence** ✅
- **not yet proven on true-positive debug grounding** ❌

That is exactly why PR-6 must exist.

---

## 5. Proposed real-symbol true-positive debug set

This section must stay grounded.

### 5.1 Evidence status for symbol selection

The current uploaded document set confirms that the target repo contains core AIOps implementation code under `src/main/java/com/mindarray/aiops/*`, and that repo-aware Ask/Debug should operate against that code. It also exposes two already-used product-facing query anchors in the existing system examples:

- “Which class is inherited by all API classes?”
- “email notification”

However, the uploaded source pack in this session does **not** include the AIOps Java file inventory itself. So the true-positive set below is split into two tiers:

- **Tier A — Repo-confirmed mandatory anchors**: selected by a deterministic scan over the checked-out AIOps repo before PR-6 is locked
- **Tier B — Already-visible query anchors**: existing product/example queries that should be converted into repo-confirmed symbol cases during Slice-1

This keeps the plan honest: no invented symbols are treated as proven facts.

### 5.2 Selection rule for the mandatory true-positive set

Before coding PR-6, run a deterministic repo scan over `src/main/java/com/mindarray/aiops/**/*` and select **5–8 symbols** that satisfy all of the following:

- implementation code, not test code
- symbol is referenced by at least one real debug-style question
- symbol name is non-trivial enough to exercise identifier matching
- file sits in real AIOps package space, not vendor/generated code
- symbol is stable enough to serve as a regression fixture

Suggested mix:

- 2 classes
- 2 methods
- 1 interface or abstract/base type
- 1 service/manager/controller class
- 1 notification/correlation-related symbol if available

### 5.3 Candidate fixture template

Use this schema for each selected debug case:

| Case ID | Symbol / method | Likely file path | Subsystem | Why this is a good debug target | Expected retrieval behavior |
|---|---|---|---|---|---|
| TPD-01 | `<real symbol>` | `src/main/java/com/mindarray/aiops/...` | `<subsystem>` | Direct symbol lookup; clear implementation home | Must appear in top-3 |

### 5.4 Mandatory seed categories

The first true-positive set should include the following categories.

#### Category A — Base API inheritance anchor

- **Target shape:** the concrete base class that is inherited by API classes, plus 1–2 child API classes
- **Source of need:** this exact query already exists in the system examples
- **Why it matters:** exercises inheritance/base-type lookup rather than plain keyword retrieval
- **Expected behavior:** base class definition in top-3; at least one child API class in expanded evidence

#### Category B — Email notification anchor

- **Target shape:** a class or method responsible for email notification flow
- **Source of need:** “email notification” already exists in the current query examples
- **Why it matters:** exercises intent-to-implementation retrieval for a business capability phrase that may not match class naming exactly
- **Expected behavior:** implementation class in top-3; supporting config/helper class optionally in top-5

#### Category C — Correlation logic anchor

- **Target shape:** real correlation class/method in the AIOps implementation tree
- **Source of need:** the current architecture spec itself uses “Why is this correlation logic risky?” as a representative debug/explain task
- **Why it matters:** this is the exact production-flavored debug scenario that triggered concern
- **Expected behavior:** selected correlation implementation file in top-3; adjacent callers/helpers in top-5

#### Category D — Service/manager/controller anchor

- **Target shape:** one operational class with a service/manager/controller suffix in AIOps package space
- **Why it matters:** tests package/path priors and common enterprise Java naming patterns
- **Expected behavior:** exact class file in top-3; same-package helpers boosted but not dominating

#### Category E — Method-level symbol anchor

- **Target shape:** one real method with CamelCase name in an implementation class
- **Why it matters:** method-level retrieval is where naive lexical search tends to crumble
- **Expected behavior:** containing file in top-3; extracted definition snippet must include the method span

### 5.5 Concrete selection workflow to make the set real

Because the actual Java symbol inventory is not present in the uploaded document corpus, the plan requires this **pre-lock deterministic extraction step**:

1. scan `src/main/java/com/mindarray/aiops/**/*.java`
2. extract package, class/interface name, public/protected method names
3. exclude test/generated/vendor files
4. produce `docs/audit/pr6_true_positive_symbol_inventory.json`
5. choose 5–8 fixtures from that inventory
6. freeze them into `docs/audit/pr6_true_positive_debug_cases.yaml`

PR-6 should not be marked complete until that fixture file exists.

---

## 6. Minimal semantic retrieval lift candidates

Only deterministic, failure-driven lifts belong here.

### 6.1 Candidate A — Symbol-first exact lookup lane

**What:**
Before generic lexical ranking, detect symbol-shaped queries and perform exact/normalized lookup against a local symbol index.

**Why:**
A debug query naming a class or method should not have to compete immediately with generic text matches.

**Deterministic behavior:**

- exact symbol hit → seed candidate set
- normalized symbol hit → secondary seed
- then merge with lexical/path/package ranking

**Status:** recommended

---

### 6.2 Candidate B — Identifier normalization

**What:**
Normalize symbol-like inputs and indexed identifiers via:

- CamelCase splitting
- case-insensitive comparison
- underscore / hyphen / punctuation normalization
- package token splitting

**Why:**
The current tracker already calls out CamelCase and symbol-aware tokenization as missing retrieval strength.

**Status:** required

---

### 6.3 Candidate C — Strong exact class/method match boost

**What:**
Add deterministic score boosts for:

- exact class name match
- exact method name match
- exact filename ↔ class-name equivalence
- exact package.class token alignment

**Why:**
True-positive debug is mostly about “I named the thing; go to the thing.”

**Status:** required

---

### 6.4 Candidate D — Selected-file / same-module / same-package bias

**What:**
When active file is provided, bias retrieval toward:

- selected file
n- same package
- same module subtree
- direct imports/callers/callees if known

**Why:**
Debug work is usually local, not repo-global. This is the cheapest deterministic semantic lift available.

**Status:** required

---

### 6.5 Candidate E — AIOps implementation path priors

**What:**
Keep and formalize the path priors already identified in the tracker:

- boost `src/main/java/com/mindarray/aiops/*`
- penalize `test/*`, `*.log`, vendor assets, metrics artifacts

**Why:**
This is already named as a non-negotiable blocker and should remain part of PR-6, not postponed.

**Status:** required

---

### 6.6 Candidate F — Stopword suppression for debug queries

**What:**
De-weight terms like:

- why
- failing
- issue
- problem
- debug
- class
- function

while preserving identifier-bearing tokens.

**Why:**
These terms are common and low-signal. They often drown the actual symbol token.

**Status:** recommended

---

### 6.7 Candidate G — Snippet extraction must prefer definition blocks

**What:**
When a class/method is matched, snippet extraction should prefer:

- method definition block
- class declaration + nearby methods
- surrounding error-handling branch if available

**Why:**
A debug answer grounded only in file presence without the relevant definition block is still brittle.

**Status:** required

---

### 6.8 Explicit non-goals

Do **not** add in PR-6:

- embeddings-first search redesign
- broad reranker integration as a dependency
- plugin UX work
- execute-path changes
- full graph retrieval architecture
- vector database redesign
- model tuning / LoRA work

Those are later moves. PR-6 is a scalpel, not a moon landing.

---

## 7. Validation design for true-positive debug cases

Validation must be request-level, deterministic, and artifact-driven.

### 7.1 Test artifact set

Create:

- `docs/audit/pr6_true_positive_debug_cases.yaml`
- `runtime/ask_validation/fixtures/pr6_true_positive_debug_requests.jsonl`
- `runtime/ask_validation/expected/pr6_true_positive_expectations.json`
- `runtime/ask_validation/reports/pr6_true_positive_debug_report.md`

### 7.2 Per-case request shape

Each case should specify:

- `task_type = DEBUG`
- natural-language request naming the real symbol or behavior
- optional `active_file`
- optional `selected_text`
- expected target file path
- expected target symbol
- expected evidence quality floor
- whether vLLM invocation is expected

### 7.3 Required validation dimensions

For every true-positive case, validate all of the following.

#### A. Retrieval

- target file appears in top-k
- target file appears in top-3 for exact symbol queries
- extracted snippets include the target symbol definition span
- non-code artifacts do not dominate the bundle

#### B. Metadata

Expected metadata should include:

- `ask_path = v1_evidence`
- evidence provenance present
- evidence quality not downgraded to `WEAK` when target file is correctly retrieved
- no `NO_SYMBOL_MATCH` on exact-symbol cases
- explicit `selected_file` / evidence entry corresponding to the target file

#### C. Debug output properties

Expected debug output should:

- mention the target symbol/class/function explicitly
- reference only retrieved evidence
- state limitations when supporting evidence is partial
- avoid generic planner text when real code evidence exists

#### D. Invocation behavior

- for local structural-only lookup cases, vLLM may be optional
- for explain/debug synthesis cases, vLLM invocation should be visible when healthy
- if vLLM is unavailable, the case must fail as “validation environment incomplete,” not pass silently

### 7.4 Pass/fail rules

#### Pass

A case passes only if:

1. target file is in top-3 for exact symbol/class queries, or top-5 for intent-style capability queries
2. top-k is majority code-bearing and not dominated by test/vendor/log artifacts
3. evidence metadata does not report symbol miss on exact-symbol cases
4. debug answer names and explains the correct symbol/file behavior from retrieved evidence
5. any limitation language is about scope, not about failing to find the obvious file

#### Fail

A case fails if any of the following occur:

- target implementation file absent from top-k
- target file only appears below rank 5 on exact symbol query
- bundle dominated by non-code artifacts
- `NO_SYMBOL_MATCH` or equivalent on a real exact-symbol case
- answer remains generic despite correct evidence being present
- answer is “honestly weak” because retrieval still missed the true-positive target

### 7.5 Recommended initial case matrix

Use a small matrix:

- 3 exact-symbol cases
- 1 method-level case
- 1 package/locality case
- 1 capability phrase case (for example notification/correlation)

That is enough to prove adequacy without boiling the ocean.

---

## 8. Files/modules likely to change

This should stay concentrated in Layer-5 retrieval / Ask validation.

### 8.1 Likely code surfaces

- `runtime/layer5/index/`
  - symbol index or identifier inventory support
- `runtime/layer5/retrieval/`
  - ranking, token normalization, path/package priors
- `runtime/layer5/evidence/`
  - definition-block-first snippet extraction
- `runtime/context_layer_service/`
  - if request plumbing must expose debug-oriented retrieval diagnostics
- `runtime/ask_service/v1_ingest.py`
  - only if metadata plumbing needs to preserve symbol-resolution fields
- `runtime/ask_validation/`
  - new true-positive validation harness and fixtures

### 8.2 Likely test surfaces

- retrieval ranking tests
- identifier normalization tests
- symbol-first candidate generation tests
- evidence quality guardrail tests
- end-to-end `/v1/ask` true-positive debug validation tests

### 8.3 Likely docs

- `docs/audit/PR6_TRUE_POSITIVE_DEBUG_AND_MINIMAL_SEMANTIC_LIFT_PLAN.md`
- `docs/audit/pr6_true_positive_debug_cases.yaml`
- `LIVE_ROADMAP_TRACKER.md` once PR-6 is implemented and validated

### 8.4 What should not change

- governance docs
- execution sandbox / Action Item 7 code
- plugin UX unless a strict metadata mismatch blocks validation visibility
- broad semantic-search architecture docs

---

## 9. Risks / non-goals

### 9.1 Risks

#### Risk A — False confidence from a tiny cherry-picked set

Mitigation:
Use 5–8 fixtures spanning different symbol shapes, not one golden screenshot case.

#### Risk B — Drift into broad retrieval redesign

Mitigation:
Keep PR-6 limited to deterministic lifts only.

#### Risk C — Mistaking path priors for true semantic adequacy

Mitigation:
Require exact-symbol and method-level cases, not only path-based wins.

#### Risk D — Validation contaminated by hidden repo state or stale copies

Mitigation:
Run only through Layer-5 evidence-first path; record workspace revision and ask path.

#### Risk E — Confusing honest insufficiency with success

Mitigation:
For true-positive fixtures, insufficiency is a failure, not a pass.

### 9.2 Non-goals

PR-6 is **not**:

- Action Item 7 execute-path validation
- plugin truthfulness workstream
- observability completion beyond what is necessary to inspect request-level debug runs
- embeddings/vector rollout
- Neo4j / LangGraph / Chroma debate
- repo-wide semantic intelligence maturity

It is the minimum move needed to stop true-positive debug from being semantically blind.

---

## 10. Recommended first coding slice

### Slice PR6-S1 — Symbol-first debug retrieval lane + fixture freeze

This should be the very first implementation slice.

#### Goal

Make exact symbol/class debug queries reliably retrieve the correct AIOps implementation file in top-3 and prove it on a frozen fixture set.

#### Scope

1. add deterministic **identifier normalization**
2. add **symbol-first exact lookup lane** in Layer-5 retrieval
3. retain/add **AIOps path priors** and non-code penalties
4. bias snippets toward **definition blocks**
5. freeze the first **5–8 true-positive debug fixtures** from the actual repo inventory
6. run request-level validation and produce a report

#### Why this slice first

Because it directly attacks the core defect without inviting architecture creep.

- smallest code surface
- highest leverage on real debug usefulness
- clean pass/fail outcome
- zero doctrine change
- zero plugin dependency

#### Acceptance criteria for PR6-S1

- exact-symbol cases hit target file in top-3
- no exact-symbol case reports `NO_SYMBOL_MATCH`
- evidence bundles are code-dominant
- debug outputs are grounded in the retrieved file/snippet
- report exists showing per-case pass/fail and rank positions

#### What comes immediately after PR6-S1

Only if needed:

- same-package / same-module locality refinement
- method-name extraction refinement
- capability phrase fallback tuning for non-exact queries

If PR6-S1 passes cleanly, Action Item 6B is substantially closed.

---

### Final closure rule

PR-6 should be considered complete only when all three are true:

1. the true-positive fixture set is frozen from real AIOps code
2. deterministic retrieval lift is implemented without broad redesign
3. true-positive debug validation passes on artifact-backed evidence

Until then, debug-path integrity is done, but debug-path adequacy is not.
