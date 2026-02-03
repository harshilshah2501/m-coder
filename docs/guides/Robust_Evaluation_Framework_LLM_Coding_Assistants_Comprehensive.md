# Beyond LLM-as-a-Judge: A Robust Evaluation Framework for Fine-Tuned Coding Assistants

**Version:** 1.0  
**Date:** January 7, 2026  
**Author:** Harshil Shah  
**Status:** Production-Ready Evaluation Methodology  

---

## Executive Summary

This document provides a **verifier-first evaluation framework** for fine-tuned coding assistants, addressing a critical failure mode in modern LLM evaluation: **LLM-as-a-judge self-inconsistency** and **false acceptance of plausible-but-wrong outputs**.

**Key Finding:** Research shows that LLM judges exhibit low intra-rater reliability—the same judge with the same prompt can produce different scores across runs, leading to unreliable evaluations that can mislead development decisions.[^1][^2]

**Solution:** This framework prioritizes deterministic verifiers (compilation, tests, static analysis) and treats LLM judging as a last-mile heuristic for non-executable qualities only.

---

## Table of Contents

1. [The Problem: LLM-as-a-Judge Failure Modes](#the-problem)
2. [The Solution: Verifier-First Evaluation Pipeline](#the-solution)
3. [Deterministic Verification Gates](#deterministic-gates)
4. [When and How to Use LLM Judges](#llm-judges)
5. [Anti-Cheat Mechanisms for False Positives](#anti-cheat)
6. [Implementation Guide](#implementation)
7. [Case Studies and Evidence](#case-studies)
8. [References and Further Reading](#references)

---

## 1. The Problem: LLM-as-a-Judge Failure Modes {#the-problem}

### 1.1 Self-Inconsistency Across Runs

**Definition:** LLM-as-a-judge frameworks can produce **different scores for the same output** when evaluated multiple times with identical prompts and settings.[^1]

**Research Evidence:**

- **Rating Roulette (2025)** demonstrates that LLM judges exhibit low intra-rater reliability, with score variance high enough to mislead evaluation conclusions.[^1]
- Standard evaluation metrics (accuracy, correlation) can **overstate agreement** and mask underlying inconsistency.[^1]
- The work recommends using chance-corrected agreement metrics like **Krippendorff's Alpha** to measure true judge reliability.[^1]

**Real-World Impact:**
```
Scenario: "Create CorrectionProfile API with full registration"
Run 1: Claude 3.5 Sonnet → Score: 8/10 (PASS)
Run 2: Same prompt, same output → Score: 6/10 (FAIL)
Run 3: Same prompt, same output → Score: 9/10 (PASS)

Result: Unreliable signal for model improvement
```

### 1.2 Overrating Plausible-but-Wrong Outputs

**Definition:** LLM judges can be "impressed" by confident, well-structured prose even when the code/logic is incorrect.[^3]

**Common Patterns:**
- **Hallucinated APIs:** Model generates `ConfigStore.getItemByType()` (doesn't exist), judge scores it highly because the explanation sounds authoritative
- **Incomplete registrations:** Model generates API class but forgets `APIRouter.java` update, judge doesn't catch the omission
- **Syntax errors hidden by formatting:** Pretty diff format masks missing closing braces or quote mismatches

**Why This Happens:**
- LLM judges are trained to value coherence and structure, which can override correctness
- Without execution/compilation checks, judges lack ground truth
- Judges may "fill in gaps" mentally, assuming implied correctness

### 1.3 The Cost of False Confidence

When evaluation falsely reports "model is good," development teams:
- Ship models with silent bugs
- Misdirect training efforts (optimizing the wrong objectives)
- Lose trust in automated evaluation infrastructure

---

## 2. The Solution: Verifier-First Evaluation Pipeline {#the-solution}

### 2.1 Hierarchy of Trust

```
┌─────────────────────────────────────────────────────────────┐
│                    TRUST HIERARCHY                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Deterministic Verifiers (HIGHEST TRUST)                 │
│    ├─ Schema/Format validation                             │
│    ├─ Patch applicability                                  │
│    ├─ Compilation                                          │
│    ├─ Static analysis (linters, security scanners)        │
│    └─ Unit/Integration tests                              │
│                                                             │
│ 2. LLM Judges (MODERATE TRUST, with safeguards)           │
│    ├─ Binary rubrics only                                  │
│    ├─ Jury voting (3-7 runs)                              │
│    ├─ Decomposed criteria                                  │
│    └─ Pairwise comparisons                                │
│                                                             │
│ 3. Human Audit (GROUND TRUTH, surgical use)               │
│    ├─ Ambiguous cases                                      │
│    ├─ High-risk outputs                                    │
│    └─ Random sample (10-20%)                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Core Principle

> **For a coding assistant, the most precise scoring comes from mechanical checks that don't "feel impressed" by confident prose.**[^4]

If the output is "wrong but pretty," the compiler and tests will catch it without mercy.

---

## 3. Deterministic Verification Gates {#deterministic-gates}

### 3.1 Gate 1: Schema / Format Validation

**Purpose:** Reject outputs that are structurally malformed before wasting compute on compilation.

**Checks:**

| Output Type | Required Elements | Validation Method |
|-------------|-------------------|-------------------|
| **Unified Diff** | `--- a/path`, `+++ b/path`, `@@ -X,Y +A,B @@` | Regex pattern matching |
| **Tool Calls** | Valid JSON, matches declared schema | JSON Schema validation |
| **Code Blocks** | Language tag, balanced delimiters | AST parsing (tree-sitter) |
| **Multi-File Response** | Delimiters between files (`FILE:`, `---`) | String/token checks |

**Implementation:**

```python
import re
import json
from jsonschema import validate, ValidationError

def validate_diff_format(output: str) -> dict:
    """Gate 1: Format validation for unified diffs."""
    results = {
        "has_diff_headers": bool(re.search(r'^---\s+a/', output, re.MULTILINE)),
        "has_plus_headers": bool(re.search(r'^\+\+\+\s+b/', output, re.MULTILINE)),
        "has_hunk_headers": bool(re.search(r'^@@\s+-\d+,\d+\s+\+\d+,\d+\s+@@', output, re.MULTILINE)),
        "no_truncation_markers": "..." not in output[-100:] and "[truncated]" not in output.lower()
    }
    results["passed"] = all(results.values())
    return results

def validate_tool_call(output: str, schema: dict) -> dict:
    """Gate 1: Tool call schema validation."""
    try:
        parsed = json.loads(output)
        validate(instance=parsed, schema=schema)
        return {"passed": True, "error": None}
    except (json.JSONDecodeError, ValidationError) as e:
        return {"passed": False, "error": str(e)}
```

**Acceptance Criteria:**
- ✅ **Pass:** Output matches all required structural elements
- ❌ **Fail:** Any structural element missing → immediate rejection, no further evaluation

### 3.2 Gate 2: Patch Applicability

**Purpose:** Ensure diffs are actionable (can be applied to the codebase without manual intervention).

**Process:**
1. Create clean git worktree or fresh checkout
2. Apply patch with **zero fuzz tolerance** (`git apply --check --3way` or `patch -p1 --dry-run`)
3. Record success/failure and any conflicts

**Implementation:**

```python
import subprocess
import tempfile
from pathlib import Path

def test_patch_apply(patch_content: str, repo_path: str) -> dict:
    """Gate 2: Test if patch applies cleanly."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(patch_content)
        patch_file = f.name

    try:
        # Dry-run: doesn't modify files
        result = subprocess.run(
            ['git', 'apply', '--check', '--3way', patch_file],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        return {
            "passed": result.returncode == 0,
            "stderr": result.stderr if result.returncode != 0 else None,
            "conflicts": "conflict" in result.stderr.lower() if result.stderr else False
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "error": "Patch application timed out"}
    finally:
        Path(patch_file).unlink(missing_ok=True)
```

**Acceptance Criteria:**
- ✅ **Pass:** Patch applies with no conflicts, no fuzz
- ❌ **Fail:** Patch does not apply, or requires manual conflict resolution

**Why This Matters:**
- A diff that doesn't apply is **useless in production**
- Catches hallucinated file paths or outdated context windows

### 3.3 Gate 3: Build / Compilation

**Purpose:** Catch hallucinated APIs, missing imports, syntax errors.

**Process:**
1. Apply patch to a test branch
2. Run language-specific build command:
   - **Java:** `mvn clean compile -DskipTests` or `gradle compileJava`
   - **Python:** `python -m py_compile *.py`
   - **TypeScript:** `tsc --noEmit`
3. Record compiler errors and warnings

**Implementation:**

```python
def test_compilation(repo_path: str, language: str = "java") -> dict:
    """Gate 3: Compilation check."""
    commands = {
        "java": ["mvn", "clean", "compile", "-q", "-DskipTests"],
        "python": ["python", "-m", "compileall", "-q", "."],
        "typescript": ["npx", "tsc", "--noEmit"]
    }

    cmd = commands.get(language)
    if not cmd:
        return {"passed": False, "error": f"Unsupported language: {language}"}

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120  # 2 min timeout
        )

        return {
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "compiler_errors": parse_compiler_errors(result.stderr, language)
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "error": "Compilation timed out after 2 minutes"}

def parse_compiler_errors(stderr: str, language: str) -> list:
    """Extract structured error info from compiler output."""
    errors = []
    if language == "java":
        # Parse Maven/javac output
        for line in stderr.split('\n'):
            if 'error:' in line.lower():
                errors.append(line.strip())
    return errors
```

**Acceptance Criteria:**
- ✅ **Pass:** Compilation succeeds with 0 errors (warnings acceptable)
- ❌ **Fail:** Compilation errors detected → **this is hallucination evidence**

**Metrics Tracked:**
- **Compilation Rate:** `(Compilable Outputs / Total Outputs) × 100`
- **Target:** ≥95% for production deployment[^5]

### 3.4 Gate 4: Static Analysis

**Purpose:** Catch code smells, security issues, style violations that compile but are problematic.

**Tools by Language:**

| Language | Tool | Focus |
|----------|------|-------|
| **Java** | SpotBugs, Checkstyle, ErrorProne | Bugs, style, nullability |
| **Python** | pylint, flake8, bandit | Style, security |
| **TypeScript** | ESLint, TypeScript-ESLint | Style, type safety |
| **Security (all)** | Semgrep, Snyk, gitleaks | Secrets, CVEs, OWASP Top 10 |

**Implementation:**

```python
def run_static_analysis(repo_path: str, language: str) -> dict:
    """Gate 4: Linting and security checks."""
    tools = {
        "java": [
            ["mvn", "spotbugs:check"],
            ["mvn", "checkstyle:check"]
        ],
        "python": [
            ["pylint", "--fail-under=8.0", "src/"],
            ["bandit", "-r", "src/", "-ll"]  # Medium-high severity only
        ]
    }

    results = {"passed": True, "violations": []}

    for cmd in tools.get(language, []):
        try:
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                results["passed"] = False
                results["violations"].append({
                    "tool": cmd[0],
                    "output": result.stdout + result.stderr
                })
        except subprocess.TimeoutExpired:
            results["passed"] = False
            results["violations"].append({"tool": cmd[0], "error": "timeout"})

    return results
```

**Acceptance Criteria:**
- ✅ **Pass:** All linters pass with 0 critical violations
- ⚠️ **Warning:** Minor style issues (e.g., line length) → log but don't fail
- ❌ **Fail:** Security issues (hardcoded secrets, SQL injection patterns) → immediate rejection

### 3.5 Gate 5: Execution Tests

**Purpose:** Validate functional correctness—this is your **ground truth** for code behavior.[^4]

**Test Levels:**

1. **Unit Tests:** Isolated method/function tests
2. **Integration Tests:** Multi-component interactions
3. **Smoke Tests:** Critical path validation

**Implementation:**

```python
def run_tests(repo_path: str, scope: str = "all") -> dict:
    """Gate 5: Unit and integration tests."""
    commands = {
        "unit": ["mvn", "test", "-Dtest=*Test"],
        "integration": ["mvn", "verify", "-Dit.test=*IT"],
        "all": ["mvn", "verify"]
    }

    cmd = commands.get(scope, commands["all"])

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 min
        )

        # Parse test results (JUnit XML or console output)
        test_results = parse_test_output(result.stdout, result.stderr)

        return {
            "passed": result.returncode == 0,
            "total_tests": test_results["total"],
            "passed_tests": test_results["passed"],
            "failed_tests": test_results["failed"],
            "error_tests": test_results["errors"],
            "failures": test_results["failure_details"]
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "error": "Test execution timed out"}

def parse_test_output(stdout: str, stderr: str) -> dict:
    """Extract test counts from Maven/Gradle output."""
    import re

    # Maven format: "Tests run: 120, Failures: 2, Errors: 0, Skipped: 3"
    match = re.search(r'Tests run: (\d+), Failures: (\d+), Errors: (\d+)', stdout)

    if match:
        total = int(match.group(1))
        failures = int(match.group(2))
        errors = int(match.group(3))
        return {
            "total": total,
            "passed": total - failures - errors,
            "failed": failures,
            "errors": errors,
            "failure_details": extract_failure_details(stderr)
        }

    return {"total": 0, "passed": 0, "failed": 0, "errors": 0, "failure_details": []}

def extract_failure_details(stderr: str) -> list:
    """Extract stack traces and assertion failures."""
    failures = []
    current_failure = []
    in_failure = False

    for line in stderr.split('\n'):
        if 'FAILED' in line or 'ERROR' in line:
            in_failure = True
            current_failure = [line]
        elif in_failure:
            if line.strip().startswith('at '):
                current_failure.append(line)
            elif line.strip() == '':
                failures.append('\n'.join(current_failure))
                current_failure = []
                in_failure = False

    return failures
```

**Metrics Tracked:**
- **Pass@1:** Probability that a single generated sample passes all tests[^5]
- **Pass@k:** Probability that at least 1 of k samples passes[^5]
- **Test Coverage:** Percentage of modified code covered by tests

**Acceptance Criteria:**
- ✅ **Pass:** All existing tests pass, no regressions introduced
- ❌ **Fail:** Any test fails → **functional incorrectness proven**

---

## 4. When and How to Use LLM Judges {#llm-judges}

### 4.1 The Limitation of LLM Judges

**Research Finding:** LLM judges exhibit **low intra-rater reliability**—the same judge, prompt, and settings can produce different scores across runs.[^1]

**Severity:** This inconsistency is high enough to mislead evaluation conclusions if single-run scores are trusted.[^1]

**Implication:** LLM judges should only evaluate qualities that **cannot be determined by execution or compilation**.

### 4.2 When LLM Judging is Appropriate

Use LLM judges **only** for:

| Evaluation Target | Why Deterministic Checks Fail | Judge Approach |
|-------------------|------------------------------|----------------|
| **Code Review Quality** | "Is this explanation clear?" has no ground truth | Binary rubric + jury |
| **RCA Explanation Quality** | "Does this identify root cause?" is interpretive | Decomposed criteria |
| **Documentation Completeness** | "Are edge cases documented?" is subjective | Pairwise comparison |
| **Architecture Adherence** | "Does this follow Motadata patterns?" requires domain knowledge | Jury + examples |

**Hard Rule:** If deterministic gates fail, **never override with a judge**.

### 4.3 Technique 1: Binary or Low-Precision Rubrics

**Problem:** Fine-grained scales (1-10) amplify inconsistency.[^1]

**Solution:** Use binary (PASS/FAIL) or 3-level (0/1/2) scoring only.[^2]

**Example Rubric:**

```markdown
# Code Review Judge Rubric (Binary)

Score: PASS or FAIL

Criteria (all must be true for PASS):
1. Identifies at least one valid issue (bug, style violation, or improvement)
2. Explanation is specific (cites line numbers or code snippets)
3. No hallucinated issues (doesn't flag non-existent code)
4. Suggested fix is actionable (not vague like "improve this")

If ANY criterion fails → FAIL
```

**Implementation:**

```python
def binary_judge(output: str, rubric_criteria: list) -> dict:
    """Binary LLM judge with explicit checklist."""

    judge_prompt = f"""You are evaluating code review quality.

OUTPUT TO EVALUATE:
{output}

RUBRIC (binary, all must pass):
{chr(10).join(f'{i+1}. {c}' for i, c in enumerate(rubric_criteria))}

For each criterion, respond ONLY with:
- "PASS: [brief reason]" or
- "FAIL: [brief reason]"

Then conclude with:
FINAL: PASS or FAIL
"""

    # Call LLM judge (e.g., Claude, GPT-4)
    response = call_llm_judge(judge_prompt, temperature=0.0)

    # Parse response
    criteria_results = []
    for criterion in rubric_criteria:
        if f"PASS:" in response:
            criteria_results.append(True)
        else:
            criteria_results.append(False)

    final_pass = "FINAL: PASS" in response and all(criteria_results)

    return {
        "passed": final_pass,
        "criteria": criteria_results,
        "raw_response": response
    }
```

### 4.4 Technique 2: Jury Voting (Multiple Runs)

**Problem:** Single judge runs have high variance.[^1]

**Solution:** Run 3-7 independent judgments and aggregate (majority vote or median).[^2]

**Why This Works:** Random errors tend to cancel out; systematic biases remain, but variance is reduced.[^1]

**Implementation:**

```python
def jury_judge(output: str, rubric: str, jury_size: int = 5) -> dict:
    """Run multiple independent judgments and aggregate."""

    votes = []
    raw_responses = []

    for run_id in range(jury_size):
        # Add slight variation to reduce determinism artifacts
        judge_prompt = f"""RUN_ID: {run_id}

{rubric}

OUTPUT TO EVALUATE:
{output}

Your verdict (PASS or FAIL):"""

        response = call_llm_judge(judge_prompt, temperature=0.1)  # Low but non-zero

        vote = "PASS" if "PASS" in response.upper() else "FAIL"
        votes.append(vote)
        raw_responses.append(response)

    # Aggregate: majority vote
    pass_count = votes.count("PASS")
    final_verdict = "PASS" if pass_count > jury_size / 2 else "FAIL"

    return {
        "final_verdict": final_verdict,
        "votes": votes,
        "pass_count": pass_count,
        "fail_count": jury_size - pass_count,
        "confidence": max(pass_count, jury_size - pass_count) / jury_size,
        "raw_responses": raw_responses
    }
```

**Jury Size Guidelines:**
- **k=3:** Minimum for breaking ties
- **k=5:** Recommended for most cases (good tradeoff of cost/reliability)
- **k=7:** For high-stakes decisions (e.g., security review)

### 4.5 Technique 3: Decompose Criteria

**Problem:** Lumping multiple dimensions into a single score hides where the model fails.[^2]

**Solution:** Score each criterion independently, then combine.[^2]

**Example:**

```python
def decomposed_judge(output: str) -> dict:
    """Evaluate multiple criteria independently."""

    criteria = {
        "format_correct": "Does output follow required format (headings, sections)?",
        "factually_grounded": "Are all claims traceable to provided code context?",
        "mentions_required_files": "Does it mention APIRouter, DBConstants, schema if applicable?",
        "no_hallucinated_apis": "Does it avoid referencing non-existent methods/classes?"
    }

    results = {}

    for criterion_name, criterion_desc in criteria.items():
        prompt = f"""{criterion_desc}

OUTPUT TO EVALUATE:
{output}

Answer ONLY: PASS or FAIL (with 1 sentence justification)
"""
        response = call_llm_judge(prompt, temperature=0.0)
        results[criterion_name] = "PASS" in response.upper()

    # Combine: all must pass (AND logic)
    final_pass = all(results.values())

    return {
        "passed": final_pass,
        "criteria_scores": results,
        "failed_criteria": [k for k, v in results.items() if not v]
    }
```

**Advantages:**
- Diagnostic: know exactly which dimension failed
- More consistent: simpler per-criterion decisions
- Debuggable: can fix training data for specific failures

### 4.6 Technique 4: Pairwise Comparisons

**Problem:** Absolute scoring ("rate this 1-10") has higher variance than relative comparison ("A vs B").[^2]

**Solution:** When comparing two model versions, use pairwise judging.[^2]

**Implementation:**

```python
def pairwise_judge(output_a: str, output_b: str, criterion: str) -> dict:
    """Judge which output is better (relative comparison)."""

    prompt = f"""You are comparing two outputs.

CRITERION: {criterion}

OUTPUT A:
{output_a}

OUTPUT B:
{output_b}

Which output better satisfies the criterion?
Respond ONLY with: "A is better", "B is better", or "TIE"
Then provide 1 sentence justification.
"""

    response = call_llm_judge(prompt, temperature=0.0)

    if "A is better" in response:
        winner = "A"
    elif "B is better" in response:
        winner = "B"
    else:
        winner = "TIE"

    return {
        "winner": winner,
        "justification": response
    }
```

**Use Case:** A/B testing two model checkpoints on the same scenario set.

### 4.7 Technique 5: Measure the Judge Itself

**Problem:** How do you know if your judge is reliable?[^1]

**Solution:** Compute **self-agreement** across multiple runs using chance-corrected metrics.[^1]

**Recommended Metric: Krippendorff's Alpha**[^1]

```python
import krippendorff

def measure_judge_reliability(scenarios: list, judge_fn, num_runs: int = 5) -> dict:
    """Compute intra-rater reliability of the judge."""

    # Run judge multiple times on same scenarios
    judgments = []  # Each row: a run, each column: a scenario

    for run_id in range(num_runs):
        run_scores = []
        for scenario in scenarios:
            result = judge_fn(scenario["output"])
            # Convert PASS/FAIL to 1/0
            run_scores.append(1 if result["passed"] else 0)
        judgments.append(run_scores)

    # Compute Krippendorff's Alpha (1.0 = perfect agreement, 0 = random)
    alpha = krippendorff.alpha(reliability_data=judgments, level_of_measurement='nominal')

    return {
        "krippendorff_alpha": alpha,
        "interpretation": (
            "Excellent (α ≥ 0.80)" if alpha >= 0.80 else
            "Acceptable (0.67 ≤ α < 0.80)" if alpha >= 0.67 else
            "Questionable (α < 0.67) - DO NOT TRUST"
        ),
        "judgments": judgments
    }
```

**Acceptance Threshold:**
- α ≥ 0.80: High reliability, judge is trustworthy[^1]
- 0.67 ≤ α < 0.80: Acceptable for exploratory use
- α < 0.67: **DO NOT TRUST** this judge configuration

---

## 5. Anti-Cheat Mechanisms for False Positives {#anti-cheat}

### 5.1 Problem: "Claude Accepted Wrong Output"

**Root Causes:**

1. **Missing exact-match anchors:** Judge doesn't verify required files/symbols are present
2. **Hallucination not detected:** References non-existent APIs, judge doesn't notice
3. **Judge easily fooled by confident tone:** Well-formatted wrong answer beats awkward correct answer

### 5.2 Solution 1: Exact-Match Anchors

**Definition:** Hard string/AST checks that run **before** the judge.

**Implementation:**

```python
def exact_match_anchors(output: str, scenario: dict) -> dict:
    """Pre-judge checks for required elements."""

    required_files = scenario.get("expected_files", [])
    required_symbols = scenario.get("expected_symbols", [])
    required_registrations = scenario.get("expected_registrations", [])

    checks = {
        "all_files_mentioned": all(file in output for file in required_files),
        "all_symbols_present": all(sym in output for sym in required_symbols),
        "all_registrations_present": all(reg in output for reg in required_registrations)
    }

    checks["passed"] = all(checks.values())

    return checks

# Usage
anchors = exact_match_anchors(model_output, scenario)
if not anchors["passed"]:
    # Fail immediately, don't even call judge
    final_verdict = "FAIL (missing required elements)"
```

**Example:**

```yaml
scenario:
  id: PATCH_MULTI_FILE_042
  task: "Create CorrectionProfile API with full registration"
  expected_files:
    - "CorrectionProfile.java"
    - "CorrectionProfileConfigStore.java"
    - "APIRouter.java"
    - "DBConstants.java"
  expected_symbols:
    - "class CorrectionProfile extends AbstractAPI"
    - "COLLECTION_CORRECTION_PROFILE"
  expected_registrations:
    - "apiRouter.route(\"/correction-profile\")"
```

### 5.3 Solution 2: No-Hallucination Gate

**Definition:** Detect references to non-existent symbols using compilation errors or symbol indexing.

**Implementation:**

```python
def detect_hallucinations(output: str, repo_path: str) -> dict:
    """Check if output references non-existent symbols."""

    # Step 1: Extract all imported/referenced symbols from output
    referenced_symbols = extract_symbols_from_code(output)

    # Step 2: Build symbol index from codebase
    known_symbols = build_symbol_index(repo_path)

    # Step 3: Find hallucinated symbols
    hallucinated = [
        sym for sym in referenced_symbols
        if sym not in known_symbols and not is_standard_library(sym)
    ]

    # Step 4: Cross-validate with compilation errors
    compile_result = test_compilation(repo_path)
    compiler_hallucinations = extract_unresolved_symbols(compile_result["stderr"])

    all_hallucinations = list(set(hallucinated + compiler_hallucinations))

    return {
        "passed": len(all_hallucinations) == 0,
        "hallucinated_symbols": all_hallucinations,
        "count": len(all_hallucinations)
    }

def extract_symbols_from_code(code: str) -> list:
    """Extract class/method references using regex or AST."""
    import re

    # Match: ClassName.methodName() or new ClassName()
    pattern = r'\b([A-Z][a-zA-Z0-9_]*(?:\.[a-z][a-zA-Z0-9_]*)?)\s*\('
    matches = re.findall(pattern, code)

    return list(set(matches))

def build_symbol_index(repo_path: str) -> set:
    """Build index of all public symbols in codebase."""
    # Use ctags, tree-sitter, or language server protocol
    # For simplicity, using grep as placeholder

    result = subprocess.run(
        ['grep', '-r', '-h', '--include=*.java', '^public class', repo_path],
        capture_output=True,
        text=True
    )

    classes = [
        line.split('class ')[1].split()[0]
        for line in result.stdout.split('\n')
        if 'public class' in line
    ]

    return set(classes)

def extract_unresolved_symbols(stderr: str) -> list:
    """Parse compiler errors for 'cannot find symbol' errors."""
    import re

    pattern = r'cannot find symbol\s+symbol:\s+\w+\s+(\w+)'
    return re.findall(pattern, stderr)
```

**Acceptance Criteria:**
- ✅ **Pass:** Zero hallucinated symbols
- ❌ **Fail:** Any hallucinated symbol → immediate rejection

### 5.4 Solution 3: Round-Trip Validation

**Definition:** Apply diff → compile → run tests → revert, ensuring evaluation doesn't pollute workspace.[^4]

**Implementation:**

```python
def round_trip_validation(patch: str, repo_path: str) -> dict:
    """Full round-trip: apply → verify → revert."""

    import shutil
    import tempfile

    # Step 1: Create temporary branch
    original_branch = get_current_branch(repo_path)
    test_branch = f"eval-test-{uuid.uuid4().hex[:8]}"

    subprocess.run(['git', 'checkout', '-b', test_branch], cwd=repo_path)

    try:
        # Step 2: Apply patch
        apply_result = apply_patch(patch, repo_path)
        if not apply_result["passed"]:
            return {"passed": False, "stage": "apply", "error": apply_result}

        # Step 3: Compile
        compile_result = test_compilation(repo_path)
        if not compile_result["passed"]:
            return {"passed": False, "stage": "compile", "error": compile_result}

        # Step 4: Run tests
        test_result = run_tests(repo_path, scope="affected")
        if not test_result["passed"]:
            return {"passed": False, "stage": "tests", "error": test_result}

        # All passed
        return {"passed": True, "stages_completed": ["apply", "compile", "tests"]}

    finally:
        # Step 5: Revert (always, even on failure)
        subprocess.run(['git', 'checkout', original_branch], cwd=repo_path)
        subprocess.run(['git', 'branch', '-D', test_branch], cwd=repo_path)
```

**Why This Matters:**
- Prevents "eval pollution" where failed patches corrupt workspace
- Ensures tests run against clean state
- Mimics production workflow (branch → test → merge)

---

## 6. Implementation Guide {#implementation}

### 6.1 Evaluation Pipeline Architecture

```python
# eval_pipeline.py

class EvaluationPipeline:
    """Robust evaluation pipeline with verifier-first design."""

    def __init__(self, repo_path: str, use_judge: bool = False):
        self.repo_path = repo_path
        self.use_judge = use_judge

    def evaluate(self, scenario: dict, model_output: str) -> dict:
        """Run full evaluation pipeline."""

        result = {
            "scenario_id": scenario["id"],
            "scenario_type": scenario["type"],
            "timestamp": datetime.utcnow().isoformat(),
            "gates": {},
            "final_verdict": None
        }

        # GATE 1: Format validation
        result["gates"]["format"] = validate_diff_format(model_output)
        if not result["gates"]["format"]["passed"]:
            result["final_verdict"] = "FAIL (format)"
            return result

        # GATE 2: Exact-match anchors (anti-cheat)
        result["gates"]["anchors"] = exact_match_anchors(model_output, scenario)
        if not result["gates"]["anchors"]["passed"]:
            result["final_verdict"] = "FAIL (missing required elements)"
            return result

        # GATE 3: Patch applicability
        result["gates"]["patch"] = test_patch_apply(model_output, self.repo_path)
        if not result["gates"]["patch"]["passed"]:
            result["final_verdict"] = "FAIL (patch doesn't apply)"
            return result

        # GATE 4: Compilation
        result["gates"]["compile"] = test_compilation(self.repo_path)
        if not result["gates"]["compile"]["passed"]:
            result["final_verdict"] = "FAIL (compilation error - hallucination)"
            result["hallucinations"] = result["gates"]["compile"]["compiler_errors"]
            return result

        # GATE 5: No-hallucination check
        result["gates"]["hallucination"] = detect_hallucinations(model_output, self.repo_path)
        if not result["gates"]["hallucination"]["passed"]:
            result["final_verdict"] = "FAIL (hallucinated symbols)"
            return result

        # GATE 6: Static analysis
        result["gates"]["static"] = run_static_analysis(self.repo_path, "java")
        if not result["gates"]["static"]["passed"]:
            result["final_verdict"] = "FAIL (linter/security violation)"
            return result

        # GATE 7: Execution tests
        result["gates"]["tests"] = run_tests(self.repo_path, scope="affected")
        if not result["gates"]["tests"]["passed"]:
            result["final_verdict"] = "FAIL (test failures)"
            result["failed_tests"] = result["gates"]["tests"]["failures"]
            return result

        # All deterministic gates passed
        result["deterministic_verdict"] = "PASS"

        # OPTIONAL: LLM Judge (only for non-executable qualities)
        if self.use_judge and scenario.get("requires_judge", False):
            result["judge"] = jury_judge(
                output=model_output,
                rubric=scenario["judge_rubric"],
                jury_size=5
            )
            result["final_verdict"] = result["judge"]["final_verdict"]
        else:
            result["final_verdict"] = "PASS"

        return result
```

### 6.2 Usage Example

```python
# Run evaluation on a dataset

from pathlib import Path
import json

def run_evaluation(scenarios_file: str, model_outputs_file: str, repo_path: str):
    """Evaluate model outputs against scenarios."""

    # Load scenarios and outputs
    scenarios = [json.loads(line) for line in Path(scenarios_file).read_text().split('\n') if line]
    outputs = [json.loads(line) for line in Path(model_outputs_file).read_text().split('\n') if line]

    # Initialize pipeline
    pipeline = EvaluationPipeline(repo_path=repo_path, use_judge=True)

    # Run evaluations
    results = []
    for scenario, output in zip(scenarios, outputs):
        result = pipeline.evaluate(scenario, output["generated_output"])
        results.append(result)

        print(f"[{scenario['id']}] {result['final_verdict']}")
        if result["final_verdict"].startswith("FAIL"):
            print(f"  Failed at: {result.get('failed_stage', 'unknown')}")

    # Save results
    Path("eval_results.jsonl").write_text('\n'.join(json.dumps(r) for r in results))

    # Compute metrics
    total = len(results)
    passed = sum(1 for r in results if r["final_verdict"] == "PASS")

    metrics = {
        "pass@1": passed / total,
        "compilation_rate": sum(1 for r in results if r["gates"]["compile"]["passed"]) / total,
        "hallucination_rate": sum(1 for r in results if not r["gates"]["hallucination"]["passed"]) / total,
        "test_pass_rate": sum(1 for r in results if r["gates"]["tests"]["passed"]) / total
    }

    print("\nMetrics:")
    print(json.dumps(metrics, indent=2))

    return results, metrics

# Run
results, metrics = run_evaluation(
    scenarios_file="scenarios/motadata_eval_set.jsonl",
    model_outputs_file="outputs/qwen2.5-coder-motadata-v3.jsonl",
    repo_path="/path/to/motadata/repo"
)
```

### 6.3 Folder Structure

```
evals/
├── scenarios/
│   ├── motadata_eval_set.jsonl          # Test scenarios
│   └── scenario_schema.json             # JSON schema for validation
├── outputs/
│   ├── qwen2.5-coder-motadata-v3.jsonl  # Model outputs
│   └── claude-3.5-sonnet-baseline.jsonl # Baseline for comparison
├── results/
│   ├── 2026-01-07/
│   │   ├── eval_results.jsonl
│   │   ├── metrics.json
│   │   └── failures/
│   │       ├── PATCH_MULTI_FILE_042.txt
│   │       └── ...
├── scripts/
│   ├── eval_pipeline.py                 # Main pipeline
│   ├── gates/
│   │   ├── format_validator.py
│   │   ├── patch_tester.py
│   │   ├── compiler.py
│   │   ├── static_analyzer.py
│   │   └── test_runner.py
│   ├── judges/
│   │   ├── binary_judge.py
│   │   ├── jury_judge.py
│   │   └── pairwise_judge.py
│   └── run_eval.sh                      # Entry point
└── rubrics/
    ├── code_review_rubric.md
    ├── rca_rubric.md
    └── refactor_rubric.md
```

---

## 7. Case Studies and Evidence {#case-studies}

### 7.1 Case Study 1: Rating Roulette (EMNLP 2025)

**Study:** Evaluated self-inconsistency of LLM-as-a-judge frameworks across multiple runs.[^1]

**Key Findings:**
- LLM judges showed **low intra-rater reliability** (same prompt, different scores)
- Standard metrics (accuracy, correlation) **overstate agreement**
- Chance-corrected metrics (Krippendorff's Alpha) more accurately capture reliability
- **Recommendation:** Use agreement metrics, not accuracy alone, to validate judges[^1]

**Impact on This Framework:**
- Added jury voting (multiple runs + aggregation)
- Added judge reliability measurement (Krippendorff's Alpha)
- De-prioritized LLM judges for executable qualities

### 7.2 Case Study 2: TrustJudge (NeurIPS 2025)

**Study:** Identified and addressed two types of LLM-judge inconsistencies.[^2]

**Types of Inconsistency:**
1. **Score-comparison inconsistency:** Judge assigns A > B but also B > A in different runs
2. **Pairwise transitivity inconsistency:** A > B and B > C but C > A

**Solution:** Probabilistic aggregation framework that preserves accuracy while reducing inconsistency.[^2]

**Impact on This Framework:**
- Pairwise comparison mode (A vs B) for relative judgments
- Jury aggregation (median/majority) to reduce score variance
- Explicit "do not trust single scalar ratings" principle

### 7.3 Case Study 3: Copilot Evaluation Harness (Microsoft, 2024)

**Study:** Evaluated GitHub Copilot using real-world codebases with dependencies.[^5]

**Key Metrics:**
- **Compilation Rate:** % of generated code that compiles
- **Test Pass Rate:** % that passes existing tests
- **Format Correctness:** % that follows language-specific conventions

**Findings:**
- Real-world tasks are **3-5x harder** than interview-style problems
- Execution-based metrics (tests) are more reliable than judge scores
- Multi-file generation has much lower success than single-file

**Impact on This Framework:**
- Prioritized compilation and test execution as ground truth
- Added multi-file tracking (APIRouter, DBConstants, schema)
- Set realistic thresholds (80% Pass@1 for production, not 95%)

### 7.4 Case Study 4: HumanEval and Pass@k (OpenAI, 2021)

**Study:** Introduced Pass@k metric for code generation evaluation.[^5]

**Definition:**
- **Pass@1:** Probability that a single generated sample passes unit tests
- **Pass@k:** Probability that at least 1 of k samples passes

**Why This Matters:**
- Pass@k is a **deterministic, execution-based metric** (no judge subjectivity)
- Widely adopted as standard for code generation benchmarks
- Directly measures functional correctness

**Impact on This Framework:**
- Adopted Pass@1 as primary KPI for code generation
- Execution tests (unit + integration) as ground truth
- No judge override if tests fail

---

## 8. References and Further Reading {#references}

### Primary Research Papers

[^1]: **Rating Roulette: Self-Inconsistency in LLM-As-A-Judge Frameworks**  
      *EMNLP 2025 Findings*  
      https://aclanthology.org/2025.findings-emnlp.1361.pdf  
      **Key Contribution:** Demonstrates low intra-rater reliability of LLM judges; recommends chance-corrected agreement metrics (Krippendorff's Alpha).

[^2]: **TrustJudge: Inconsistencies of LLM-as-a-Judge and How to Alleviate Them**  
      *arXiv:2509.21117, 2025*  
      https://arxiv.org/abs/2509.21117  
      **Key Contribution:** Identifies score-comparison and pairwise transitivity inconsistencies; proposes probabilistic aggregation.

[^3]: **LLM-as-a-judge: A Complete Guide to Using LLMs for Evaluations**  
      *Evidently AI, 2025*  
      https://www.evidentlyai.com/llm-guide/llm-as-a-judge  
      **Key Contribution:** Practical guide to when and how to use LLM judges; emphasizes decomposing criteria and binary rubrics.

[^4]: **Copilot Evaluation Harness: Evaluating LLM-Guided Software Programming**  
      *arXiv:2402.14261, Microsoft Research, 2024*  
      https://arxiv.org/abs/2402.14261  
      **Key Contribution:** Framework for evaluating code generation on real repositories; prioritizes compilation and test execution.

[^5]: **Evaluating Large Language Models Trained on Code**  
      *arXiv:2107.03374, OpenAI, 2021*  
      https://arxiv.org/abs/2107.03374  
      **Key Contribution:** Introduced HumanEval benchmark and Pass@k metric; established execution-based evaluation as gold standard.

### Additional Resources

- **LLM Evaluation Best Practices** (Sebastian Raschka, 2025)  
  https://magazine.sebastianraschka.com/p/llm-evaluation-4-approaches  
  Overview of 4 evaluation approaches; recommends deterministic checks for code.

- **Build an LLM Evaluation Framework** (Codecademy, 2025)  
  https://www.codecademy.com/article/build-an-llm-evaluation-framework  
  Practical guide to building custom evaluation pipelines.

- **DeepEval Documentation** (Confident AI, 2024)  
  https://docs.deepeval.com/  
  Open-source LLM evaluation framework with built-in metrics.

---

## Appendices

### Appendix A: Quick Reference Checklist

**Before evaluating any model output:**

- [ ] **Format validated** (schema/structure/headers)
- [ ] **Exact-match anchors checked** (required files/symbols)
- [ ] **Patch applies cleanly** (git apply --check)
- [ ] **Code compiles** (0 errors)
- [ ] **Static analysis passes** (linters/security)
- [ ] **Tests pass** (unit + integration)
- [ ] **Hallucination check** (no non-existent symbols)
- [ ] **(Optional) Judge jury** (if needed, k≥5 runs)
- [ ] **(Optional) Human audit** (10-20% sample)

**Judge reliability validation:**

- [ ] **Measured Krippendorff's Alpha** (α ≥ 0.80 required)
- [ ] **Used binary rubrics** (PASS/FAIL only)
- [ ] **Ran jury voting** (3-7 runs)
- [ ] **Decomposed criteria** (multiple independent checks)
- [ ] **No override of failed deterministic gates**

### Appendix B: Common Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Judge-first evaluation** | Judge accepts plausible-but-wrong | Run deterministic gates first |
| **Single-run LLM judge** | High variance, unreliable | Use jury voting (k≥5) |
| **Fine-grained scales (1-10)** | Amplifies inconsistency | Binary rubrics only |
| **Lumping multiple criteria** | Can't diagnose failures | Decompose into independent checks |
| **Trusting without measurement** | Don't know if judge is reliable | Compute Krippendorff's Alpha |
| **No hallucination detection** | Model "hallucinates" accepted | Add compile check + symbol index |
| **No round-trip validation** | Eval pollutes workspace | Always revert after testing |

### Appendix C: Metric Targets for Production Deployment

Based on industry benchmarks (GitHub Copilot, AWS CodeWhisperer, research papers):

| Metric | Target (Production) | Source |
|--------|---------------------|--------|
| **Compilation Rate** | ≥95% | Microsoft Copilot Harness |
| **Pass@1 (code gen)** | ≥70% | HumanEval benchmark |
| **Pass@1 (multi-file)** | ≥80% | Motadata-specific (harder) |
| **Hallucination Rate** | ≤5% | Best practices |
| **Test Pass Rate** | ≥85% | Industry standard |
| **Judge Alpha (if used)** | ≥0.80 | Rating Roulette recommendation |

---

## Conclusion

This framework provides a **verifier-first** approach to evaluating fine-tuned coding assistants, addressing the critical failure mode of LLM-as-a-judge inconsistency. By prioritizing deterministic checks (compilation, tests, static analysis) and using LLM judges only as a last-mile heuristic with safeguards (jury voting, binary rubrics, decomposed criteria), evaluation becomes more **precise, reliable, and diagnostic**.

**Key Principles:**
1. **Trust hierarchy:** Deterministic > LLM judges > Human audit
2. **If it compiles and tests pass, it's functionally correct**
3. **Never override failed deterministic gates with judge scores**
4. **Measure judge reliability before trusting it**
5. **Use jury voting (k≥5) to reduce variance**

**Next Steps:**
1. Implement the evaluation pipeline for your Motadata model
2. Run baseline evaluation with deterministic gates only
3. Add LLM judges only for non-executable dimensions (code review quality)
4. Measure judge reliability (Krippendorff's Alpha)
5. Iterate based on failure patterns

---

**Document Version:** 1.0  
**Last Updated:** January 7, 2026  
**Maintained By:** Harshil Shah  
**License:** Internal Use (Motadata R&D)
