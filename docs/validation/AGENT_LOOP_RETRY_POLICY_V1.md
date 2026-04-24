# AGENT_LOOP_RETRY_POLICY_V1

## Scope

Discovery-only policy for future acting-system loop and retry controls.  
No loop behavior is changed by this document.

## Policy Goals

- Bound execution deterministically.
- Prevent hidden retry behavior.
- Surface failures explicitly and early.
- Preserve full auditability for each loop decision.

## Iteration Limits (Future Contract)

- Global hard cap per request: `max_iterations` (must be explicit in envelope/policy).
- Per-class retry caps:
  - proposal-validation retry cap
  - tool-retryable-failure cap
  - policy-recheck cap (normally zero retries unless explicitly allowed)
- Budget consumption is monotonic and never replenished in-loop.

## Retry Rules

1. **No silent retries**: every retry attempt must emit a ledger event with reason code.
2. **Single-cause retries only**: each retry must name one deterministic cause class.
3. **No retry on forbidden classes**:
   - policy denied/refused
   - schema incompatibility
   - approval missing/expired
   - illegal state transition
4. **Retry scope must narrow**: retries cannot expand tool scope, file scope, or privilege level.

## Stop Rules

Immediate terminal stop on:

- budget exhausted
- explicit refusal posture
- hard policy violation
- illegal transition/state corruption
- unresolved validation mismatch
- repeated identical failure beyond class cap

Terminal outcomes must map to stable reason codes.

## Explicit Failure Surfaces

Future loop implementation must return:

- terminal state
- terminal reason code
- reason-code chain for prior attempts
- last action/result refs (if any)
- execution truth summary (`not_run`, `blocked`, `executed`, `failed`)

No opaque "unknown failure" responses.

## Auditability Requirements

Per iteration, ledger should include:

- proposal ref
- decision ref
- tool dispatch/result refs (if any)
- retry classification
- budget before/after
- state transition (`from`, `to`, `event`)

Auditors must be able to reconstruct why each retry happened and why loop terminated.

## Anti-Looping Guards

- Detect repeated equivalent proposals by normalized hash and stop after threshold.
- Detect repeated equivalent tool failures and force terminal decision.
- Reject retry attempts that only re-run identical denied actions.

## Implementation Prerequisites

1. Standard retry classification taxonomy.
2. Stable equivalence/hash scheme for proposals and tool requests.
3. Formal budget model (shared across loop controller and decision engine).
4. Invariant tests for "no silent retry" and "monotonic budget".
5. Operations runbook for interpreting retry/terminal reason chains.
