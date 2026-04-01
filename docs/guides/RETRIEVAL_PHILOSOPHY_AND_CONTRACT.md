# 📘 Retrieval Philosophy & Contract

## Motadata AI Coding Assistant — Layer-5 (Workspace Intelligence)

---

## 1. Purpose of This Document

This document defines the **non-negotiable philosophy, requirements, and constraints** for the retrieval system used in the Motadata AI Coding Assistant.

It exists to prevent:

* accidental regression into generic search behavior
* misuse of external tools without alignment
* hidden non-determinism or unverifiable ranking logic

This is not an implementation guide.
This is a **contract**.

---

## 2. The Core Misconception

At first glance, retrieval appears to be a solved problem.

Industry provides:

* Elasticsearch / Lucene (BM25)
* Vector search / embeddings
* Code search tools (Sourcegraph, OpenGrok)

These systems solve:

> “Find documents relevant to a query”

But our system must solve:

> **“Select the exact code evidence that explains or fixes a system behavior — deterministically.”**

This distinction is fundamental.

---

## 3. Problem Definition (What We Are Solving)

Given:

* a large production codebase (AIOps)
* a user query (debug, explain, trace, analyze)

We must:

1. retrieve **correct implementation files**
2. prioritize **production code over noise**
3. ensure **top-ranked evidence is trustworthy**
4. provide **explainable ranking decisions**
5. maintain **deterministic behavior**

---

## 4. Why Existing Solutions Fall Short

### 4.1 Lexical Search (BM25 / Lucene)

**Optimized for:**

* documents
* logs
* frequency-based relevance

**Failure in our context:**

* logs and JSON dominate due to repetition
* no distinction between code and non-code
* no intent awareness

---

### 4.2 Vector / Embedding Search

**Optimized for:**

* semantic similarity
* fuzzy matching

**Failure in our context:**

* non-deterministic behavior
* difficult to audit or reproduce
* no guarantee of exact grounding

---

### 4.3 Code Search Tools

**Optimized for:**

* navigation
* symbol lookup

**Failure in our context:**

* weak intent modeling
* not designed for evidence selection
* not integrated into reasoning pipelines

---

## 5. Our Requirements (Non-Negotiable)

The retrieval system must satisfy ALL of the following:

---

### 5.1 Deterministic Behavior

* Same query + same repo → same result
* No randomness
* No model-dependent variability

---

### 5.2 Code-First Prioritization

* `src/main/java/**` must dominate ranking for code/debug queries
* Logs, tests, metrics, vendor assets are secondary or suppressed
* Retrieval must reflect **system responsibility**, not text density

---

### 5.3 Explainable Scoring

Each result must be decomposable into:

* path contribution
* basename contribution
* content contribution
* symbol contribution
* policy bias (priors, penalties, boosts)

No opaque scoring.

---

### 5.4 Zero Hallucination Dependency

* The reasoning layer depends entirely on retrieved evidence
* Retrieval must be **trustworthy enough to eliminate guessing**

---

### 5.5 Auditability

At any time, we must answer:

> “Why did this file rank #1?”

This includes:

* scoring breakdown
* policy contributions
* suppression decisions

---

### 5.6 Reproducibility

* Required for debugging production incidents
* Required for validation and testing
* Required for trust in the system

---

### 5.7 Intent-Aware Behavior

The system must differentiate query intent:

| Intent Type   | Retrieval Behavior  |
| ------------- | ------------------- |
| debug / code  | strongly code-first |
| exploratory   | broader tolerance   |
| documentation | relaxed constraints |

Intent influences ranking policy.

---

## 6. Retrieval Is Not Search

Traditional mindset:

> “Which files mention these tokens most?”

Correct mindset:

> **“Which files are most likely responsible for this behavior?”**

This requires:

* structural awareness
* symbol understanding
* file-class prioritization
* intent-driven ranking

---

## 7. Key Failure Mode (Observed in Real Repo)

From real audit:

* logs and JSON files outrank Java classes
* content repetition dominates scoring
* correct files appear in top-3 but not top-1

Interpretation:

> Retrieval is no longer blind, but still not authoritative.

This is unacceptable for production.

---

## 8. Design Principles

---

### 8.1 Content Must Not Dominate Blindly

* Large files (logs, JSON) must not win due to repetition
* Content contribution must be:

  * capped
  * class-aware
  * optionally disabled for noise classes

---

### 8.2 File Classes Are Not Equal

The system must explicitly distinguish:

* core_aiops_code
* supporting_code
* tests
* logs
* vendor_static
* generated_metrics_data

Ranking must reflect this hierarchy.

---

### 8.3 Noise Must Be Controlled

For code/debug intent:

* logs and metrics must not compete directly with code
* noise can appear only:

  * as fallback
  * or in lower ranks

---

### 8.4 Structure Over Volume

Prefer:

* path alignment
* symbol matches
* subsystem relevance

Over:

* raw token frequency

---

### 8.5 Deterministic Policy > Heuristics

All behavior must be:

* config-driven
* versioned
* testable

No hidden rules.

---

## 9. What We Are Building

Not:

* a search engine
* a vector retrieval system
* a code browser

We are building:

> **A Deterministic Evidence Selection Engine for Code Reasoning**

This means:

* retrieval is part of reasoning
* ranking is part of correctness
* scoring is part of trust

---

## 10. Relationship with External Tools

External tools may be used for:

* indexing speed
* tokenization
* parsing support

But:

> **They must not define ranking behavior.**

We always:

* override ranking logic
* enforce policy
* maintain determinism

---

## 11. Anti-Patterns (Strictly Forbidden)

* Blind BM25 usage
* Content-heavy scoring without class control
* Embedding-only retrieval
* Non-deterministic ranking
* “Good enough” top-k without top-1 correctness
* Hiding failures with broader retrieval

---

## 12. Success Criteria

Retrieval is considered production-ready when:

* top-1 accuracy is consistently high on real repo
* noise does not dominate top-k
* evidence is code-dominant for code intent
* failures are explainable and minimal
* results are reproducible across runs

---

## 13. Guiding Principle

> **Search finds mentions.
> Retrieval must find responsibility.**

---

## 14. Final Statement

We are not reinventing the wheel.

We are building a system where:

* correctness matters more than relevance
* determinism matters more than flexibility
* explainability matters more than convenience

Because the output of retrieval is not a list of files.

It is:

> **the foundation of reasoning, debugging, and decision-making.**

