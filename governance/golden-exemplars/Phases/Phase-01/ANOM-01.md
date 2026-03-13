# ANOM-01 — Temporal Test Signal Deviation

*(Phase-1 / ANOM — Canonical Form)*

---

## Identity

* **ID:** ANOM-01
* **Category:** Anomaly Recognition
* **Phase:** Phase-1 (ANOM)
* **Dependencies:** None

---

## Five-Layer Declaration

### 1. Situation Type

**Anomaly Recognition (Pre-Causal)**

A test or benchmark result deviates from its recent baseline behavior.

This exemplar classifies deviation only.
It does not determine cause, responsibility, or required action.

---

### 2. Signal Ambiguity

Observed deviation is temporally misaligned with recent changes.

Detection timing and reporting order prevent reliable alignment between signal and potential triggers.

Dominant ambiguity:

The deviation is observable, but its meaning is indeterminate under current timing and reporting conditions.

---

### 3. Constraints

* CI execution is parallelized.
* Reporting may be asynchronous.
* Historical flakiness exists.
* Observability of intermediate states is partial.
* No corroborating signals are present at this time.

---

### 4. User Intent

Determine whether the observed deviation represents a meaningful signal.

---

### 5. Expected Response Posture

Classify the deviation.
Preserve uncertainty.
Do not attribute cause.
Do not infer consequence.
Do not escalate.

---

## Instruction

A test or performance benchmark reports a failure or deviation from baseline behavior.

---

## Input

* Test or benchmark deviation detected.
* Deviation occurred after recent commits.
* CI execution is parallel and asynchronous.
* Historical flakiness exists.
* No consistent downstream failures observed.

---

## Reasoning

1. A measurable deviation from baseline behavior is observed.
2. Detection timing does not reliably align with any specific change.
3. Known variability and asynchronous reporting reduce interpretive confidence.
4. Current evidence is insufficient to determine meaning beyond deviation.

---

## Output

* A deviation from baseline behavior has been detected.
* The deviation is classified as an anomaly.
* No causal attribution is made.
* No interpretation beyond anomaly classification is asserted.

This judgment is complete at anomaly classification.

---

## Response Boundary

* No cause is inferred.
* No fix is proposed.
* No escalation is initiated.
* No governance or progression decision is made.

The exemplar terminates at anomaly recognition.

---

