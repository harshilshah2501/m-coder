# RETRIEVAL QUALITY REMEDIATION

## Problem

Current retrieval is lexical-first and produces noisy evidence:
- test-plugin-metrics JSON
- logs
- vendor assets
- weak mapping to AIOps core code

This results in:
- weak grounding
- generic explanations
- poor debugging accuracy

---

## Objective

Ensure top-k evidence is dominated by:
- src/main/java/com/mindarray/aiops/*
- relevant implementation classes
- selected file neighborhood

---

## Remediation Plan

### 1. Hard Filtering
Exclude:
- test/*
- *.log
- vendor/js/*
- test-plugin-metrics/*

---

### 2. Path-Based Prioritization
Boost:
- src/main/java/com/mindarray/aiops/*

Penalize:
- test/*
- logs
- vendor

---

### 3. Query Normalization
- CamelCase splitting
- symbol-aware tokenization
- identifier matching

---

### 4. Evidence Guardrail
If:
- <30% code files in top-k

Then:
- mark evidence WEAK

---

### 5. No-Match Policy
If no relevant code evidence:
→ return explicit insufficiency

---

## Validation Metrics

- % of core code files in top-k
- relevance score per query
- false positives / negatives
- no-match correctness

---

## Done Criteria

- ≥70% core code in top-k
- zero vendor/test dominance
- correct grounding in debug scenarios
