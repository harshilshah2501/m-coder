# Iteration 10 Training TODO

**Created:** December 17, 2025  
**Purpose:** Capture improvements needed for next training iteration based on real-task evaluation

---

## Priority Issues from Real Task Testing

### 1. Model Output Quality - Diff Line Wrapping (HIGH PRIORITY)

**Problem:**
The Iter9 model wraps long lines in unified diff output, breaking the patch format and causing application failures.

**Example of broken output:**
```diff
- *  28-Feb-2025                Darshan Parmar          MOTADATA-
5215: SonarQube Suggestions Resolution
```

**Should be:**
```diff
- *  28-Feb-2025                Darshan Parmar          MOTADATA-5215: SonarQube Suggestions Resolution
```

**Impact:**
- 3/4 diffs failed to apply in real task testing
- Success rate: 25% (only 1/4 files patched successfully)
- Post-processing workaround implemented but unreliable

**Root Cause:**
Model learned to wrap lines, likely from:
- Training data with wrapped examples
- Tokenization boundaries causing breaks
- Context window handling during generation

**Training Fix Options:**

1. **Add diff-specific training examples:**
   - Include well-formed unified diffs in training set
   - Emphasize: "Never wrap diff lines mid-content"
   - Show examples of correct vs incorrect diff formatting

2. **Prompt engineering in fine-tuning:**
   ```
   System: When generating unified diffs, each diff line must be complete.
   Never wrap lines with '+', '-', or ' ' prefixes across multiple lines.
   Long lines should remain on a single line.
   ```

3. **Data augmentation:**
   - Generate synthetic diffs with long lines
   - Include Java files with 120+ char lines
   - Train model to keep these intact

4. **Validation during training:**
   - Add diff format validation to training pipeline
   - Filter/reject training samples with wrapped diffs
   - Bias towards correctly formatted examples

**Dataset Additions Needed:**
- [ ] Collect 100+ examples of well-formed unified diffs
- [ ] Include diffs with lines >100 characters
- [ ] Add negative examples (wrapped diffs) with corrections
- [ ] Annotate with "CORRECT FORMAT" / "INCORRECT FORMAT" labels

**Success Criteria for Iter10:**
- [ ] Generate valid unified diffs without line wrapping
- [ ] 90%+ patch application success rate
- [ ] Handle lines up to 200 characters without breaking
- [ ] Maintain diff format markers (+, -, @@) correctly

---

### 2. Context Window Optimization (MEDIUM PRIORITY)

**Problem:**
16K token limit truncates output for 4-file changes

**Impact:**
- Last file (Patch8025.java) incomplete
- Need 20K+ tokens for complete 4-file diffs

**Training Improvements:**
- Teach model to be more concise in diffs
- Focus on minimal context (3 lines before/after)
- Avoid redundant context in hunks

---

### 3. Full File vs Diff Generation (EVALUATION NEEDED)

**Current:** Model generates unified diffs (token-efficient)
**Alternative:** Generate complete modified files

**Tradeoffs:**

| Approach | Pros | Cons |
|----------|------|------|
| Unified Diffs | Token-efficient (5-10x less) | Parsing complexity, wrapping issues |
| Full Files | Simple parsing, reliable | High token cost, context pollution |

**Recommendation for Iter10:**
- Train model to handle BOTH formats
- Add format selection to prompt:
  ```
  Generate output as: [unified-diff | full-file]
  ```
- Let user choose based on file size/complexity

---

### 4. Code Quality in Baseline (DOCUMENTATION ISSUE)

**Not a model issue** - Task YAML generation has escaping bugs

**Action:** Fix convert_jira_to_yaml.py (separate from model training)

---

## Training Data Improvements for Iter10

### High-Value Additions

1. **Diff Format Examples (200+ samples)**
   - Well-formed unified diffs
   - Multi-file changes
   - Long lines (100-200 chars)
   - Complex hunks with context

2. **Real JIRA Task Solutions**
   - Use the 91 candidates (score ≥70) from benchmark
   - Include git commit messages
   - Show before/after code
   - Include rationale/explanation

3. **Error Recovery Examples**
   - Show how to handle wrapped lines
   - Demonstrate format validation
   - Include self-correction examples

### Training Prompts to Add

```markdown
Example 1: Unified Diff with Long Lines
========================================
Task: Refactor database constants

Output:
File: src/main/java/com/company/DBConstants.java
```diff
@@ -10,7 +10,7 @@
 public class DBConstants {
     // Query status constants used across the application for monitoring query execution state
-    public static final String DB_QUERY_STATUS_SUCCEEDED = "succeeded";  // Indicates successful query execution without errors
+    public static final String DB_QUERY_STATUS_SUCCEEDED = "completed_successfully";  // Updated to be more descriptive about execution state
     public static final String DB_QUERY_STATUS_FAILED = "failed";
 }
```

Explanation: Lines with long comments remain on single lines. Do not wrap.
```

---

## Evaluation Metrics for Iter10

**Add to benchmark:**
- [ ] Diff format validation score
- [ ] Patch application success rate
- [ ] Average line length in diff output
- [ ] Token efficiency (tokens per successful file)

**Target Improvements:**
- Diff application: 25% → 90%+
- Format validation: New metric, target 95%+
- Token efficiency: Maintain or improve
- Overall task success: Current baseline → +20%

---

## Implementation Checklist

### Pre-Training
- [ ] Collect diff format training examples
- [ ] Create validation scripts for diff format
- [ ] Add diff-specific prompts to training set
- [ ] Augment dataset with long-line examples

### During Training
- [ ] Monitor diff format quality in validation
- [ ] Track patch application success rate
- [ ] Compare Iter9 vs Iter10 on same tasks

### Post-Training
- [ ] Run full benchmark (5 real tasks minimum)
- [ ] Measure patch application success rate
- [ ] Document improvements/regressions
- [ ] Update training strategy based on results

---

## Notes from December 17, 2025 Testing

**Test Task:** e0a7fdff9d3a (Rank 1, 100 points)
- 4 files, SNMP/Vert.x/Database refactoring
- Iter9 generated 15,724 tokens
- **Result:** 1/4 files successfully patched (25%)
- **Primary failure mode:** Line wrapping in diff output

**Key Insight:**
> "This is actually a model output quality issue, not a parsing issue. The model needs to learn not to wrap diff lines, or we need to post-process to rejoin them."

The infrastructure works. The model needs better training on diff format discipline.

---

## References

- [DECEMBER_17_SESSION.md](../RAG-Datastore/docs/DECEMBER_17_SESSION.md) - Session details
- [RAG_STATUS_DEC17.md](../RAG-Datastore/evaluation/RAG_STATUS_DEC17.md) - Test results
- [Real task YAMLs](../RAG-Datastore/evaluation/motadata_tasks/tasks/) - Task definitions
- [Benchmark JIRA](../RAG-Datastore/training-artifacts/benchmark_jira.jsonl) - 2,731 candidates

---

**Next Actions:**
1. Complete Iter9 baseline evaluation (all 5 real tasks)
2. Analyze failure patterns across all tasks
3. Build Iter10 training dataset with diff format examples
4. Retrain and benchmark
