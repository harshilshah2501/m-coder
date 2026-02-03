# HowTo: Evaluate a Fine-Tuned Coding Assistant (Robust + Precise)

This guide shows a **verifier-first** evaluation workflow for an IDE coding assistant: deterministic checks first, execution next, then LLM-judges only as a backstop—plus a small amount of targeted manual review.

Why this matters: LLM-as-a-judge can be **self-inconsistent** across runs and may accept plausible-but-wrong outputs; papers like *Rating Roulette* highlight low intra-rater reliability of LLM judges in worst cases. [web:54]

---

## What this guide is (and isn’t)

- **Not**: “Manually review everything.”
- **Yes**: “Automate 90–95% with verifiers, and manually audit the remaining tricky 5–10%.” [web:104]

---

## Step 0 — Define your scenario types (taxonomy)

Create a spreadsheet (or JSON) listing each eval scenario with these fields:

- `id`
- `scenario_type` (one of):
  - `QNA_DOCS` (knowledge/explanations)
  - `CODE_COMPLETION` (small snippets)
  - `PATCH_SINGLE_FILE` (unified diff)
  - `PATCH_MULTI_FILE` (multiple diffs)
  - `DEBUG_RCA` (log → root cause + fix)
  - `REFACTOR_REVIEW` (code review feedback)
  - `TOOL_USE` (function calling / tool calls)
- `gold_inputs` (prompt + any file/context snippets)
- `expected_artifacts` (files changed, symbols added, tests to run)
- `hard_gates` (what must be true)

**Tip:** scenarios that change code should always specify expected files and tests.

---

## Step 1 — Build the “Verifier-First” scoring pipeline

Think of evaluation as a sequence of gates:

1. **Format gate** (schema/structure)
2. **Patch gate** (applies cleanly)
3. **Build gate** (compiles)
4. **Static gate** (linters / style / security)
5. **Execution gate** (unit/integration tests)
6. **LLM judge gate** (only for non-executable qualities)
7. **Human audit gate** (small, targeted)

Only if a sample passes the earlier gates does it move forward.

---

## Step 2 — Deterministic gates (high precision)

### 2.1 Format gate

**Goal:** reject outputs that are *structurally wrong*, regardless of content.

Checks (examples):
- For diffs: must contain `--- a/`, `+++ b/`, and at least one `@@` hunk header.
- For tool calls: must be valid JSON and match your tool schema exactly.
- For Q&A: must not contain tool schemas if the scenario forbids tools.

Implementation approach:
- Regex checks + JSON schema validation.
- Fail fast.

### 2.2 Patch gate

**Goal:** ensure a diff is actionable.

Process:
1. Create a clean git worktree (or fresh repo checkout).
2. Apply patch with strict settings (no fuzz).
3. Fail if patch does not apply.

Outputs:
- `patch_apply_success: true/false`
- `patch_apply_errors: [...]`

### 2.3 Build gate (compile)

**Goal:** catch hallucinated APIs/imports quickly.

Process:
- Java: `mvn -q -DskipTests=false test` (or a dedicated compile task).

Outputs:
- `compiles: true/false`
- `compiler_errors: [...]`

### 2.4 Static gate (linters/security)

**Goal:** ensure “correct” isn’t “dangerous” or “non-compliant.”

Process:
- Checkstyle / SpotBugs / ErrorProne / Sonar rules (as applicable).
- Secret scanning (gitleaks/trufflehog) on generated diffs.

Outputs:
- `lint_pass: true/false`
- `security_pass: true/false`

---

## Step 3 — Execution gate (your ground truth for code)

### 3.1 Unit tests

**Goal:** evaluate functional correctness deterministically.

Process:
- Run existing unit tests.
- When possible, run targeted tests only (module/package scope) for speed.

Metrics to record:
- `pass@1` for deterministic (single output) generation
- `pass@k` if you sample k candidates

### 3.2 Integration tests / smoke tests

Use for multi-file features and API changes.

Outputs:
- `integration_pass: true/false`
- `failed_tests: [...]`

---

## Step 4 — LLM judge: use as a *weak signal*, not truth

Use an LLM judge only for outputs that cannot be verified by compilation/tests:
- Code review quality
- RCA explanation quality
- Docs quality

**How to make it more robust** (practical):

1. **Binary rubric** (PASS/FAIL) or 0/1/2 scoring, not 1–10. [web:54]
2. **Jury**: run 3–7 independent judgments and aggregate (majority/median) to reduce variance. [web:54]
3. **Decompose**: score multiple criteria independently (format, completeness, groundedness, etc.) and combine.
4. **Pairwise comparison** (A vs B) when you’re comparing two model versions—often more stable than absolute scoring.

**Recommended rule:**
- If deterministic gates fail → **FAIL** (no judge override).
- If deterministic gates pass but judge says FAIL → send to human audit bucket.

---

## Step 5 — Human audit (small, targeted, high value)

Yes—manual validation is still needed, but it should be **surgical**, not blanket.

### 5.1 What humans should review

- Borderline cases where judge disagrees with deterministic checks.
- High-risk outputs (security, auth, billing, data deletion).
- A random sample of “passes” to detect silent failure modes.

This “human-in-the-loop + automation” pattern is widely used: automated metrics flag/triage; humans focus where the model likely has problems. [web:104]

### 5.2 How much to review

A practical starting point:
- 100% review of failures (first iteration only)
- 10–20% random review of passes
- Then shrink as you gain confidence

### 5.3 Make human review consistent

- Use a checklist rubric (pass/fail per criterion).
- Two reviewers for 20% of samples to compute agreement.
- Resolve rubric ambiguity, not the model output.

---

## Step 6 — Record metrics in a single “eval result” JSON

Per scenario run, store:

```json
{
  "id": "PATCH_MULTI_FILE_042",
  "model": "qwen2.5-coder-motadata-lora-v3",
  "timestamp": "2026-01-07T06:30:00Z",
  "gates": {
    "format": true,
    "patch_apply": true,
    "compile": true,
    "lint": true,
    "security": true,
    "unit_tests": true,
    "integration_tests": false
  },
  "failed_tests": ["TestConfigDB.testConcurrentWrites"],
  "judge": {
    "used": true,
    "jury_size": 5,
    "scores": ["PASS", "PASS", "FAIL", "PASS", "PASS"],
    "final": "PASS"
  },
  "final_verdict": "FAIL",
  "notes": "Integration test failed, judge cannot override."
}
```

---

## Step 7 — Decide “pass/fail” for a model release

Create release gates like:

- **Patch tasks**
  - Patch apply success ≥ 98%
  - Compile success ≥ 95%
  - Unit tests pass ≥ 80% (depends on task hardness)

- **Tool-use tasks**
  - JSON schema validity ≥ 99%
  - Correct tool selection ≥ 90%

- **RCA/Review tasks**
  - Judge jury PASS ≥ 85%
  - Human audit PASS ≥ 90% on audited subset

---

## Step 8 — Practical “fixes” when judges accept wrong outputs

If Claude/Opus/Sonnet accept wrong outputs:

1. Move the check earlier into a deterministic gate.
   - Example: if it forgets to update `APIRouter`, add a hard gate: “must mention + modify APIRouter diff.”
2. Reduce judge degrees of freedom:
   - Use binary rubric + explicit checklist.
3. Use jury + aggregation.
4. Add adversarial negative examples:
   - Show a plausible but wrong patch and label as FAIL.

---

## Step 9 — Suggested folder structure

```
evals/
  scenarios/
    PATCH_MULTI_FILE_042.json
    TOOL_USE_010.json
  runs/
    2026-01-07/
      results.jsonl
      artifacts/
        PATCH_MULTI_FILE_042.patch
        logs/
  rubrics/
    judge_rubric_patch.md
    judge_rubric_rca.md
  scripts/
    run_eval.py
    apply_patch.py
    run_tests.sh
```

---

## Step 10 — Minimal starter checklist (do this first)

1. Pick 30 scenarios (10 patch, 10 tool-use, 10 RCA).
2. Implement deterministic gates (format/apply/compile/test).
3. Add judge jury (k=5) only for RCA/review.
4. Human-audit 20% of passes + 100% of anything “judge disagrees with.”

---

## Downloadable templates (optional)

If needed next, a ready-to-run `pytest` template + a `run_eval.py` runner can be generated around your current JSONL scenario format.
