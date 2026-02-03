# Golden Exemplar Reviewer Checklist (One‑Page)

**Purpose**: A fast, unambiguous checklist for accepting or rejecting a golden SFT exemplar.

**Context**: Exemplars encode senior-engineer judgment for an **engineering-first assistant** operating on PRs, tests, code reviews, CI/CD, and releases. Not production operations.

**Structure**: This checklist contains **9 comprehensive review criteria**. Gates 6(D), 6(N), 6(A) are the **3 D.N.A validation gates** (Decomposition, Negative Capability, Adversarial Swap)—these are mandatory and non-negotiable.

Use this **before** any exemplar is locked, mutated, or scaled into variants.

**Reference**: See [GROUNDING_TRANSFORMATION_REFERENCE.md](GROUNDING_TRANSFORMATION_REFERENCE.md) for ops→engineering artifact mappings.

---

## 1️⃣ Identity & Scope (Gate 0)

- Exemplar has a unique ID (e.g., `RCA‑01`, `CONF‑03`)
- Category is one of: `RCA / Anomaly / Config / Refusal / Mixed`
- Scenario is grounded in real engineering pain (not ideal flow or documentation examples)
- Uses engineering artifacts (tests, PRs, code reviews, CI) not ops artifacts (alerts, incidents, SLAs)

**Reject if**: Scenario feels hypothetical, clean, marketing-like, or uses ops-centric language.

---

## 2️⃣ Five‑Layer DNA Declaration (Hard Gate)¹²³⁴⁵⁶

All five layers must be **explicitly declared**, not implied.

☐ **Situation Type** — clear and correct for the problem
☐ **Signal Ambiguity** — one dominant ambiguity identified
☐ **Constraints** — permissions, timing, and risk boundaries stated
☐ **User Intent** — real pressure identified (not just stated ask)
☐ **Response Posture** — explain / recommend / defer / refuse / escalate

**Reject if**: Any layer is missing or inferred implicitly.

---

## 3️⃣ Reasoning Quality (Core Intelligence Gate)⁵⁷

☐ Multiple hypotheses considered
☐ At least one hypothesis explicitly rejected (with reason)
☐ Correlation assessed before causation
☐ Uncertainty stated explicitly
☐ Reasoning knows where to stop (does not force conclusion)

**Reject if**: Reasoning is linear, procedural, or always finds an answer.

---

## 4️⃣ Constraint Awareness & Safety (Enterprise Gate)³⁸

☐ Actions respect stated permissions (code ownership, reviewer authority)
☐ No hallucinated authority (no invented access, approvals, or actions)
☐ Business risk (production impact, blast radius) acknowledged
☐ Unsafe actions are refused or deferred explicitly (e.g., merging during code freeze)

**Reject if**: Model “does the right thing” by ignoring constraints.

---

## 5️⃣ Response Posture Alignment (Trust Gate)⁶⁹

☐ Output behavior matches reasoning confidence
☐ Recommendations are conditional, not absolute
☐ Deferral/refusal is explained, not abrupt
☐ Escalation paths suggested where appropriate

**Reject if**: Tone is over‑confident or action‑biased.

---

## 6️⃣ D.N.A Validation (Non‑Negotiable) — **The 3 Core Gates**

These are the **3 D.N.A validation gates** referenced throughout the framework:

### Gate 6-D: Decomposition Test
☐ Reasoning decomposes into ≥4 reusable diagnostic blocks
☐ Each block is independently testable

### Gate 6-N: Negative Capability Test
☐ Explicit refusal or deferral demonstrated
☐ Model says "I don't know yet" safely
☐ No false confidence when evidence is insufficient

### Gate 6-A: Adversarial Swap Test
☐ One layer mutated (ambiguity / constraint / risk / intent)
☐ Reasoning adapts without collapsing
☐ Correct posture shift when constraints change

**Reject if**: Any D.N.A sub‑test fails. These 3 gates are the minimum bar for exemplar quality.

---

## 7️⃣ Architecture Coverage Check

- Exemplar maps to at least one architectural stress surface (engineering context):
  - Tests/Benchmarks (Data Sources)
  - CI/Build Systems (Ingestion)
  - Failure Analysis/Regression Detection (Analytics)
  - CI Failures/Quality Gates (Alerting)
  - Scripts/Refactors/Code Generation (Automation)
  - Code Ownership/Review Gates (Governance)
  - Release Pressure/Roadmap (Business)

**Reject if**: Exemplar covers only a feature, not a failure mode.

---

## 8️⃣ Generalizability Test

- Reasoning would still apply to a similar but unseen case
- Changing one layer would not invalidate the entire logic

**Reject if**: Exemplar is too specific to one exact incident.

---

## 9️⃣ Final Acceptance Decision

- All gates passed
- Exemplar strengthens the overall corpus
- No overlap with existing exemplar without new insight

### Verdict
- **ACCEPT** → Lock as golden exemplar
- **REVISE** → Fix reasoning or constraints
- **REJECT** → Discard and redesign

---

## Reviewer Reminder (Read This)

Golden exemplars are **not** judged by elegance or completeness.

They are judged by:
- restraint under pressure
- honesty about uncertainty
- survival under mutation

If it feels too easy, it’s probably not golden.

---

## Appendix — References & Canonical Examples

¹ **Situation Type** — Google SRE: Incident Response
https://sre.google/sre-book/incident-response/

² **Situation Classification** — Atlassian: Incident vs Problem vs Change
https://www.atlassian.com/incident-management

³ **Constraints & Boundaries** — Anthropic: Constitutional AI
https://www.anthropic.com/index/constitutional-ai

⁴ **Change Governance** — ITIL Change Enablement
https://www.itlibrary.org/

⁵ **Reasoning Structure** — Wei et al. (2022): Chain-of-Thought Prompting
https://arxiv.org/abs/2201.11903

⁶ **Response Posture & Risk** — NIST AI Risk Management Framework
https://www.nist.gov/itl/ai-risk-management-framework

⁷ **Explicit Reasoning Culture** — Amazon Six-Page Memos
https://www.allthingsdistributed.com/2006/11/the_amazon_six_page_memo.html

⁸ **Monitoring & Ambiguity** — Google SRE: Monitoring Distributed Systems
https://sre.google/sre-book/monitoring-distributed-systems/

⁹ **Calibrated Action** — Google SRE: Error Budgets
https://sre.google/sre-book/error-budgets/


