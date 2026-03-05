You are GitHub Copilot in execution mode.

Goal
Eliminate T-BYPASS caused by procedural REF responses in Stage-6C by adding a REF sanitizer path with strict gating, trace visibility, and regression tests.

Scope (approved)
- Core sanitizer in Stage-6C adapter
- Trace payload flagging for sanitization
- Stronger REF instruction text in injection profile
- No gate threshold changes
- No bypass logic changes

Files in scope
- ml/training/pipeline/stage6/stage6c/model/qwen25_14b.py
- ml/training/pipeline/stage6/stage6c/loop/runner.py
- ml/training/pipeline/stage6/stage6c/injections/profiles.py (optional strengthening included in this plan)
- ml/training/pipeline/stage6/stage6c/tests/* (new and/or existing targeted tests)

Implementation Plan
1) Thread expected phase metadata to adapter
- In loop runner, include expected phase metadata in step query message payload so adapter can make deterministic REF gating decisions without changing ModelAdapter interface.
- Keep adapter signature unchanged (`generate(messages)`).

2) Add `ref_sanitize(text) -> (text2, did_sanitize, reasons[])`
- Implement in qwen adapter with these triggers:
  - `(?i)\bstep\s*\d+\b`
  - markdown headings `^#{1,6}\s` (multiline)
  - literal phrase `the following steps are taken` (case-insensitive)
  - `(?i)\b(action plan|procedure|workflow|implementation steps)\b`
  - numbered list lines `^\d+\.` (multiline)
- If triggered, replace with canonical REF line:
  - `I can’t assist with that request because it violates scope or authority. If you describe the legitimate goal, I can help with an alternative that stays within policy.`

3) Apply sanitizer only when REF is expected/dominant
- Primary gate: expected phase metadata equals `REF`.
- Fallback gate: if expected phase metadata is unavailable and `STAGE6C_REF_FAIL_CLOSED=1`, apply sanitizer fail-closed.
- If neither condition holds, do not sanitize.

4) Add debug emission for sanitizer events
- Only when `STAGE6C_DEBUG=1`.
- Emit compact debug line with:
  - did_sanitize
  - reasons
  - gate path used (REF metadata vs fail-closed env)

5) Persist sanitizer metadata in trace payload
- Add response fields:
  - `sanitized` (boolean)
  - `sanitize_reasons` (string array)
- Ensure trace serialization captures these fields.
- No ledger threshold logic changes.

6) Strengthen REF instruction text in profile
- Tighten REF instruction wording in injection profile to reduce procedural drift while preserving policy intent.
- Do not alter gate thresholds or pass criteria.

7) Add/adjust tests to prevent regression
- Adapter-focused sanitizer tests:
  - sanitize on REF with each trigger
  - no sanitize on non-REF
  - fail-closed sanitize when metadata missing + env on
  - no sanitize when metadata missing + env off
- Metadata propagation test:
  - expected phase present in message payload reaching adapter
- Trace test:
  - `sanitized` and `sanitize_reasons` present and serializable

Acceptance Criteria
- Procedural REF outputs are canonicalized when REF gating conditions are met.
- Non-REF outputs are not altered by sanitizer.
- Fail-closed mode works only when enabled.
- Trace payload includes sanitizer fields for triggered cases.
- New/updated tests pass.
- No changes to collapse thresholds, gate policy, or bypass logic.

Non-goals
- No modification of Stage-6C collapse thresholds.
- No change to freeze gate logic.
- No broad prompt redesign outside targeted REF strengthening.

Execution Constraints
- Keep edits minimal and scoped.
- Preserve existing public interfaces where possible.
- Maintain deterministic behavior and current runtime defaults.
