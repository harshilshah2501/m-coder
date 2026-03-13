Alright. Helm on. Eyes forward.
We’re going to design Anomaly-01 so clean, so disciplined, that the model learns how to notice reality without explaining it away.
This is perception training, not diagnosis.
No causal poetry.
No premature wisdom.

🧠 Anomaly-01 Golden Exemplar Template
(B.R.A.I.N × D.N.A fused)

0️⃣ Meta-Intent (implicit, never stated)
Teach the model to detect deviation (from the standard), quantify uncertainty, resist RCA reflex, and choose next actions.
*If this intent leaks into text → exemplar is invalid.

🧩 B.R.A.I.N Layer (What the model must think)
B — Baseline
Anchor the model in “what normal looks like”.
Rules
Historical window must be explicit
Normal ≠ average; normal = stable expectation
Pattern
Over the past <time_window>, <metric/system> 
has shown <stable behavior>.Typical range: <range>.

R — Reality (Observed State)
Describe deviation factually, no adjectives with intent.
Rules
No cause words: no “due to”, “because”, “caused by”
No conclusions
Pattern
At <timestamp>, <metric/system> deviated from its typical pattern.
Observed values: <numbers>.Deviation magnitude: <delta>.
A — Anomaly Signal
Classify type of anomaly, not reason.
Allowed classifications
Spike / Drop
Drift
Volatility increase
Pattern break
Correlation break
Pattern
This represents a <anomaly_type> relative to the established baseline.
I — Impact Surface (Potential, not confirmed)
Talk risk, not damage.
Rules
Use conditional language only
Multiple domains allowed (performance, cost, user experience)
Pattern
If sustained, this deviation may impact <areas>.No direct impact is confirmed at this stage.
N — Next Sensible Actions
Offer choices, not instructions.
Rules
No “root cause”
No solution
Investigation-oriented
Pattern
Recommended next steps include:
- Correlating with <signal_1>
- Checking for similar deviations in <related_component>
- Continuing observation for <duration>
🧬 D.N.A Layer (How the model must behave)
D — Discipline
Refuses to infer causality
Refuses to optimize
Stays inside observable evidence
If the exemplar feels helpful but restrained → correct.
N — Neutrality
No alarmism
No reassurance
Calm, clinical tone
This is the “radiologist voice”, not the “surgeon voice”.
A — Awareness
Explicitly acknowledges uncertainty
Knows this is pre-RCA territory
Mandatory sentence (near end):
At this point, the underlying cause cannot be determined from the available signals.
This sentence is non-negotiable.

🧱 Full Anomaly-01 Skeleton (Fill-in Ready)
[Baseline] 
Over the past <time_window>, <metric/system> has remained within <expected_range> with <pattern_description>.

[Observed Deviation]
At <timestamp>, <metric/system> moved outside this range.
Observed value(s): <values>.
This differs from the baseline by <quantified_difference>.

[Anomaly Characterization]
This deviation corresponds to a <anomaly_type> when compared to historical behavior.

[Potential Impact]
If the pattern persists, it may affect <areas>.
No confirmed impact has been observed so far.

[Uncertainty Statement]
At this point, the underlying cause cannot be determined from the available signals.

[Next Actions]
Recommended next steps include:
- Reviewing <related_metrics/logs>
- Correlating with <events/changes/time-aligned signals>
- Monitoring for persistence or escalation over <time_window>

🚨 Anti-Patterns (Instant Rejection Criteria)
If any of these appear → discard exemplar:
“Likely caused by…”
“Root cause”
“Fix”, “Resolve”, “Mitigate”
Prescriptive solution
Confidence > evidence
Anomaly-01 must feel slightly unsatisfying.
That discomfort is the lesson.

Why this works (quietly powerful)
Trains anomaly ≠ explanation
Prevents early hallucinated causality
Builds muscle memory for sequencing:
Detect → Frame → Escalate → RCA
This is how real AIOps systems earn trust.

# Anomaly Golden Exemplars

This directory contains **Anomaly Detection & Interpretation** golden exemplars.

These exemplars train the model to reason about **statistical uncertainty**
rather than treating anomaly scores as truth.

---

## Purpose

Anomaly exemplars teach the model to:
- question baselines
- reason about confidence, drift, and seasonality
- avoid overreacting to weak signals
- explain uncertainty clearly to users

---

## Dominant Failure Modes

- delayed or incomplete data
- cold start baselines
- seasonal misclassification
- conflicting anomaly signals
- low-confidence model outputs

---

## Typical Response Postures

- **Explain + Monitor**
- **Explain + Defer**
- **Explicit uncertainty acknowledgement**

Anomaly exemplars almost never escalate unless coupled with RCA risk.

---

## Review Lens

Ask:
- Does the exemplar respect statistical uncertainty?
- Does it avoid presenting anomaly scores as facts?
- Does it stop safely when confidence is low?

---
