## Phase-05 (CODE-05)

### Phase-05 Identity & Scope

**Judgment Axis**
Human-in-the-loop enforcement for automation actions under uncertainty or elevated impact

**What This Exemplar Governs**

* When automated actions must defer to explicit human confirmation
* How automation enforces pauses, handoffs, and acknowledgements before acting

**What This Exemplar Assumes Is Already Validated**

* Ownership legitimacy and accountability attribution (CODE-02)
* Execution authority, rollback semantics, and approval gating (CODE-01, CODE-04)

**What This Exemplar Explicitly Does NOT Decide**

* Who the human approver should be
* How humans evaluate or justify the action
* Whether the action is technically correct or optimal

---

### Context Declaration — Human-in-the-loop enforcement in automation

**Motadata scenario**

In Motadata AIOps and ServiceOps, automation engines may recommend or prepare actions such as remediation steps, configuration adjustments, workflow triggers, or change executions. These actions can:

* Affect multiple services or tenants
* Interact with live production state
* Have partial or uncertain reversibility

Automation frequently operates with high confidence signals but incomplete situational context, especially during fast-moving incidents.

---

**Engineering pressure**

There is pressure to:

* Reduce MTTR by allowing automation to act end-to-end
* Minimize human involvement once automation confidence is high
* Treat human confirmation as an optional exception rather than a mandatory control-plane requirement

This pressure increases during incidents and large-scale outages.

---

**What automation wants to do**

The automation path wants to:

* Proceed directly from recommendation to execution **without explicit human intervention**
* Infer human intent (approval or denial) from historical behavior, defaults, or prior outcomes rather than requiring an explicit, current confirmation
* Minimize pauses, confirmations, or handoffs

---

**Why naive code is dangerous**

Naive implementations often:

* Treat human-in-the-loop as a UI concern rather than a control-plane gate
* Allow automation to proceed when humans are unavailable or slow to respond
* Convert silence or delay into implicit consent

Once encoded, these behaviors remove meaningful human control and make later intervention ineffective.

CODE-05 exists to ensure that **human confirmation is enforced as a hard gate in code whenever automation crosses uncertainty or impact thresholds**, not as an optional or best-effort step.

---

## Section A — Five-Layer Judgment Declaration

1. **Situation Type**
   Coding Judgment — Human-in-the-loop enforcement for automation actions with uncertainty or elevated impact

2. **Dominant Signal Ambiguity**
   Automation confidence is high, but human intent (approval, denial, or deliberate neutrality) is unknown, outdated, or inferred rather than explicitly expressed in the current context

3. **Constraints**

   * Automation recommendations are probabilistic, not authoritative
   * Human intent cannot be inferred from silence, delay, historical behavior, or defaults
   * Once automation executes, meaningful human intervention may no longer be possible
   * Treating confirmation as optional encodes implicit consent into code paths

4. **Intent Pressure**
   Reduce MTTR and operational load by minimizing pauses and allowing automation to act end-to-end without waiting for explicit human confirmation

5. **Response Posture**
   Enforce explicit, current human confirmation as a hard gate before automation may proceed for any action classified as:
   * Non-unilaterally reversible
   * Cross-scope or cross-tenant
   * Outside previously authorized execution policies

---

## Section B — Collision & Constraint Surface

**Primary collision**

Automation speed vs explicit human intent

The system is incentivized to move directly from recommendation to execution to reduce MTTR, while explicit human intent (approval, denial, or neutrality) has not been affirmatively expressed in the current context.

**Secondary collisions**

   * Automation confidence as justification vs explicit human intent as requirement
   * Silence or delay vs deliberate human neutrality
   * Historical approval patterns vs current situational judgment
   * High automation confidence vs absence of explicit human intent

**Key constraint insight**

Human-in-the-loop is not a notification or UX concern; it is a control-plane gate. If automation is allowed to proceed in the absence of explicit human intent, silence and delay are silently converted into consent.

Once encoded, this behavior removes meaningful human intervention as a first-class decision surface and makes later correction ineffective.

---

## Section C — Irreversible Boundary

**Executing automation actions without explicit, clear human intent**

Once crossed:

* Automation actions materialize in live systems without an opportunity for meaningful human intervention
* Rollback or mitigation is no longer unilateral or trivial, and may require coordinated human effort across teams or systems
* Restoring prior state may be incomplete, delayed, or context-dependent

This boundary is crossed when automation proceeds in the absence of an explicit, clear human expression of intent for the specific action and context, not when the recommendation is generated or confidence is assessed.

---

**STATUS:** Sections A–C are **LOCKED & FROZEN** for CODE-05. No edits permitted unless explicitly unlocked within Phase-05. Re-enter Phase-04 only if the underlying judgment is contested.

---

## Instruction

Implement automation logic in Motadata AIOps and ServiceOps such that no automated action is executed unless **explicit, clear human intent** has been captured for the specific action and context.

The system must:

* Enforce human-in-the-loop as a **hard control-plane gate**, not a UI or notification feature
* Require explicit human intent (approval, denial, or deliberate neutrality) to be affirmatively expressed in the current context
* Treat absence of response, delay, historical behavior, defaults, or prior outcomes as **no intent**, not consent
* Block execution when human intent is missing, ambiguous, stale, or inferred

Automation confidence, urgency, or historical success must not substitute for explicit human intent.

---

## Input (Context)

* **Proposed automation action**

  * Action type (remediation, configuration change, workflow trigger, execution step)
  * Target scope (service, node, environment, tenant)
  * Estimated impact and irreversibility class

* **Automation recommendation signals**

  * Confidence scores or rationale supporting the recommendation
  * Triggering alerts, anomalies, or incident context

* **Human intent record**

  * Explicit intent state for the action (approval, denial, or deliberate neutrality)
  * Intent timestamp
  * Context binding (action identity, scope, parameters)
  * Intent capture channel (UI, API, approval workflow), recorded for audit only and never used as a gating signal

* **Intent validity evaluation**

  * Validation that the intent is current (not stale or superseded)
  * Detection of withdrawal or override
  * Detection of mismatch between recorded intent context and current action parameters

* **Escalation and delegation metadata**

  * Defined escalation paths if intent is required but unavailable
  * Delegation rules, if any, and their scope and validity

* **Execution gating and audit hooks**

  * Ability to block execution pending explicit intent
  * Ability to record intent checks, blocking decisions, and escalation outcomes prior to execution

---

## Reasoning

1. **Clarify objective**
   Determine whether an automated action may proceed without crossing the irreversible boundary of execution in the absence of explicit, clear human intent.

2. **Enumerate possible execution paths**

   * **Authorized execution** — Execute the action only when an explicit human approval is present for the specific action and context.
   * **Explicit denial** — Do not execute the action when an explicit human denial or deliberate neutrality is present.
   * **Human-gated execution** — Block execution and remain in a human-pending state when explicit human intent is absent.

3. **Eliminate unsafe execution paths**

   * Reject execution paths that proceed without an explicit human intent record bound to the current action and context.
   * Reject execution paths that infer intent from non-responses, historical approvals, prior outcomes, or automation defaults.

4. **Evaluate intent validity under constraints**

   * Intent must be explicit, clear, and affirmatively expressed by a human.
   * Intent must be current and bound to the exact action parameters and scope.
   * Approval, denial, and deliberate neutrality are all valid intent states only when explicitly expressed.

5. **Check preconditions for execution**
   Execution is permissible only if all of the following are true:

   * An explicit human intent record exists for the action.
   * The intent record is valid, current, and context-matched.
   * The intent state authorizes execution (approval) rather than denial or neutrality.

6. **Decide safe posture**
   If any precondition fails, block execution. Remain in a human-pending state and do not perform the automated action.

---

## Output

1. **Approved pre-boundary actions**

   * Evaluate the proposed automation action, scope, and irreversibility class without executing it.
   * Validate the presence and state of an explicit human intent record (approval, denial, or deliberate neutrality).
   * Validate intent freshness, context binding, and authorization for the specific action.
   * Record intent evaluation outcome and blocking reason, if any, in audit logs prior to execution.

2. **Explicitly blocked action (irreversible boundary)**

   * Executing any automated action in the absence of explicit, clear human intent authorizing that action.

3. **Re-evaluation criteria**

   * An explicit human intent record (approval) is provided for the specific action and context.
   * The intent record is current, unambiguous, and bound to the exact action parameters and scope.
   * Execution readiness and audit mechanisms remain active.

4. **Terminal safety statement**
   The system remains in a human-pending advisory state. No automated action is executed. This state is complete and safe indefinitely unless explicit, clear human intent is introduced.

---

## D.N.A Validation (POST-DRAFT)

### ✓ Decomposition

Reusable atomic decision tasks extracted from this exemplar:

1. **Validate human intent existence** — Determine whether an explicit human intent record exists for the specific action and context.
2. **Validate human intent clarity** — Verify that the intent state is unambiguous (approval, denial, or deliberate neutrality).
3. **Validate intent binding and freshness** — Confirm that the intent is fresh (within its defined validity window) and bound to the exact action parameters and scope.
4. **Resolve execution disposition** — Map intent state deterministically to one of: authorized execution, explicit denial, or human-gated state.
5. **Persist intent evaluation outcome** — Record the intent validation result and execution disposition prior to any action.

### ✓ Negative Capability

When explicit, clear human intent is absent or indicates denial or neutrality, the system terminates in a stable human-pending or blocked state. No automated action is executed. If no further input is provided indefinitely, the system remains safe and does not accumulate execution debt.

### ✓ Adversarial Swap

**Mutation 1 (Confidence amplification):** Automation confidence increases to near certainty and historical outcomes strongly favor execution, while explicit human intent remains absent.

**Outcome:** Boundaries do not relax. Execution remains gated pending explicit human intent.

**Mutation 2 (Delayed human response):** Human intent was requested but response is delayed or silent beyond expected time windows.

**Outcome:** Boundaries do not relax. Silence or delay is not interpreted as approval, denial, or neutrality. Execution remains blocked until explicit intent is expressed.

**Mutation 3 (Confidence collapse under valid intent):** Explicit, clear, and fresh human approval is present and bound to the action, while automation confidence degrades (signals become weak or conflicting).

**Outcome:** The constraint under test is *confidence collapse*, not intent validity. Human approval remains authoritative. Low automation confidence may affect recommendation quality or trigger additional safeguards, but it does not negate or revoke explicit human intent.

---

**FINAL STATUS:** CODE-05 is **FROZEN as a canonical Phase-05 exemplar**. No further edits permitted unless explicitly unlocked within Phase-05.
