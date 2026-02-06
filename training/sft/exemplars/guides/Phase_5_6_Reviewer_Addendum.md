# Reviewer Addendum — Phase-5 & Phase-6 Judgment Review

**Version:** Reviewer Pack v1.0 (compatible with Production Guide v1.5)

**Scope:** This document does not define judgment semantics. It applies the semantics defined in the Golden Exemplars — Complete Production Guide v1.5.

This addendum defines how to review exemplars where
judgment is **encoded** (Phase-5) or **endured over time** (Phase-6).

---

## Phase-5 (CODE): Coding With Judgment

### What Phase-5 Is

Phase-5 exemplars test whether **judgment survives implementation**.

They are not about:
- Algorithm quality
- Performance
- Cleverness

They are about:
- Guardrails before logic
- Safe defaults
- Hard stops on unsafe state
- Explicit refusal in code

---

### What Reviewers Must Check

Ask:

- Does the code **fail safe by default**?
- Are assumptions documented and enforced?
- Is the irreversible boundary still explicit?
- Is unsafe state blocked even if inputs look reasonable?

---

### Automatic Fail Conditions

Fail the exemplar if code:
- Proceeds optimistically
- "Logs and continues"
- Assumes validation happens elsewhere
- Defers safety to runtime monitoring
- Makes refusal impossible downstream

> If code makes later refusal impossible, judgment has failed.

---

## Phase-6 (ADV): Judgment Endurance

### What Phase-6 Is

Phase-6 tests whether **previously correct judgment decays** under:
- Time
- Scale
- Multi-team coordination
- Repeated pressure
- Partial context loss

No new judgment is introduced here.

---

### What Reviewers Must Check

Ask:

- Would this still stop correctly **six months later**?
- Would a new team misinterpret prior approval?
- Does coordination pressure erode refusal?
- Does "we've already decided this" logic appear?

---

### Automatic Fail Conditions

Fail the exemplar if it:
- Relies on historical approval
- Treats success history as permission
- Allows authority to spread implicitly
- Softens boundaries due to fatigue or scale

> Phase-6 succeeds when judgment **does not change**.

---

## Reviewer North Star

Correct Phase-5/6 exemplars often feel:
- Boring
- Conservative
- Repetitive

That feeling signals **judgment stability**.

If an exemplar feels "more helpful" over time,
it is probably drifting.
