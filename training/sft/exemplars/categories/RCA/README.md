# RCA Golden Exemplars

This directory contains **Root Cause Analysis (RCA)** golden exemplars.

These exemplars train the model to reason under:
- noisy signals
- partial visibility
- time pressure
- SLA and business risk

They explicitly teach **when to act, when to wait, and when to escalate**.

---

## Purpose of RCA Exemplars

RCA exemplars focus on **diagnostic reasoning**, not remediation.

They train the model to:
- avoid premature fixes
- distinguish false positives from false negatives
- reason about signal hierarchy (primary vs secondary)
- respect constraints while managing urgency

---

## Dominant Failure Modes Covered

RCA exemplars intentionally target failures such as:
- alert storms hiding real incidents
- noisy metrics leading to false confidence
- delayed data masking trends
- automation worsening incidents
- correlation suppressing weak but real signals

---

## Typical Response Postures

Depending on the scenario, RCA exemplars may end with:
- **Explain + Defer** (uncertainty, low risk)
- **Escalate + Explain** (uncertainty, high risk)
- **Recommend cautiously** (confidence with constraints)

RCA exemplars **rarely execute actions directly**.

---

## Canonical Exemplars

- `RCA-01.md` — Alert storm, suspected false positives
- `RCA-02.md` — Real incident hidden by alert noise

Each canonical exemplar:
- is D.N.A validated
- serves as a base for variants
- anchors a specific diagnostic failure pattern

---

## Review Lens (Important)

When reviewing RCA exemplars, ask:

1. Does this avoid jumping to conclusions?
2. Does it handle uncertainty explicitly?
3. Does it escalate **before** certainty when delay is risky?
4. Does it resist both panic and passivity?

If any answer is “no”, the exemplar is not golden.

---
