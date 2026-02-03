# Phase 4.1: Human Correction Workflow Guide

**Date:** December 18, 2025  
**Status:** In Progress  
**Objective:** Capture high-quality correction traces from failed Iter9 tasks to train Iter10

---

## Overview

This phase involves manually correcting the 4 failed tasks from Iter9 baseline, documenting every step to generate training data that teaches the model how to solve multi-file coding problems.

### Why This Matters

- **Iter9 Baseline:** 0/4 tasks passed (0%)
- **Goal:** Capture the **process** of solving, not just the final code
- **Training Data:** Each correction becomes a training example showing reasoning + solution
- **Expected Improvement:** Iter10 should reach 40-60% pass rate after training on corrections

---

## Workflow Steps

### Step 1: Start Correction Session

For each failed task, use the correction helper:

```bash
cd /home/harshil/Harshil-PoCs/RAG-Datastore

# Task 1: refactored_code_loggers
python evaluation/correction_helper.py --task refactored_code_loggers

# This will:
# 1. Load the task YAML and Iter9 baseline result
# 2. Create a workspace with baseline files
# 3. Add model's failed attempt
# 4. Spawn interactive Docker sandbox
```

### Step 2: Analyze Model's Failure

Inside the sandbox:

```bash
# 1. Review the task
cat README.md

# 2. Check model's attempt
cat MODEL_ATTEMPT.txt

# 3. Try to compile
mvn compile

# 4. Document errors in CORRECTION_LOG.md
vim CORRECTION_LOG.md
```

### Step 3: Incremental Fixes

**Critical:** Document EVERY step, don't just fix everything at once.

Example workflow:
```bash
# Fix 1: Add missing import
vim src/main/java/com/mindarray/api/SomeClass.java
# Add: import com.mindarray.X;

# Test
mvn compile

# Document in CORRECTION_LOG.md what you fixed and why

# Fix 2: Initialize variable
vim src/main/java/com/mindarray/api/SomeClass.java
# Add initialization

# Test again
mvn compile

# Continue until compilation succeeds...
```

### Step 4: Verify Solution

```bash
# Run the verification script
bash verify.sh

# Should show: PASS ✅
```

### Step 5: Exit and Save Trace

```bash
# Exit sandbox
exit

# The helper script will ask if you want to save the trace
# Answer 'yes' to save correction trace to evaluation/correction_traces/
```

---

## What to Document in CORRECTION_LOG.md

### ✅ Good Documentation

```markdown
## Step 3: Fix #1 - Missing Import Statement

**File:** src/main/java/com/mindarray/api/SNMPOIDGroup.java
**Issue:** Compiler error - cannot find symbol: Vertx
**Root Cause:** Model generated code without import statement
**Fix:** Added import io.vertx.core.Vertx;

\`\`\`diff
@@ -1,5 +1,6 @@
 package com.mindarray.api;
 
+import io.vertx.core.Vertx;
 import io.vertx.core.json.JsonObject;
\`\`\`

**Test:**
\`\`\`bash
mvn compile
\`\`\`

**Result:** ✅ Compilation succeeded
```

### ❌ Poor Documentation

```markdown
Fixed imports and stuff
```

### Why Detail Matters

The training data needs to teach the model:
1. **What** went wrong (specific error)
2. **Why** it went wrong (root cause)
3. **How** to fix it (specific change)
4. **Verification** that fix worked

---

## Task Correction Priority

Based on Iter9 baseline failures:

| Priority | Task ID | Files | Response Size | Focus Area |
|----------|---------|-------|---------------|------------|
| 1 | `refactored_code_loggers` | 4 | 2,024 chars | Small response → likely incomplete |
| 2 | `topology_testcases_parallelism` | 3 | 2,275 chars | Setup failed → environment issue |
| 3 | `refactored_snmp` | 4 | 3,985 chars | Medium response → logic errors |
| 4 | `metric_plugin_tag_assignment` | 4 | 19,340 chars | Large response → may be closer |

**Recommendation:** Start with Task 1 (simplest) to validate workflow, then do Task 4 (most complex).

---

## Common Patterns to Capture

### Pattern 1: Missing Imports
```java
// Model forgets:
import com.mindarray.api.AbstractMonitor;
import io.vertx.core.Vertx;
```

### Pattern 2: Uninitialized Variables
```java
// Model writes:
private SNMPClient client;

// Should be:
private SNMPClient client;

public Constructor() {
    this.client = new SNMPClient(config);
}
```

### Pattern 3: Incomplete File Generation
```java
// Model generates 1 file when 4 are needed
// Document: "Model only created X.java, missing Y.java, Z.java"
```

### Pattern 4: Incorrect Vert.x Patterns
```java
// Model uses:
Thread.sleep(1000);

// Should use:
vertx.setPeriodic(1000, handler -> { ... });
```

### Pattern 5: Missing Error Handling
```java
// Model writes:
snmpClient.get(oid);

// Should be:
try {
    snmpClient.get(oid);
} catch (SNMPException e) {
    logger.error("SNMP error", e);
}
```

---

## Time Estimates

Per task:
- **Analysis:** 15-30 minutes (understand requirement, review model attempt)
- **Fixing:** 30-60 minutes (incremental compilation fixes)
- **Verification:** 10-15 minutes (run tests, verify pass)
- **Documentation:** 15-30 minutes (write correction log)

**Total per task:** 1.5-2.5 hours  
**All 4 tasks:** 6-10 hours (1-2 workdays)

---

## Output Files

After completing all corrections:

```
evaluation/
├── correction_traces/
│   ├── refactored_code_loggers.json          # Correction trace 1
│   ├── metric_plugin_tag_assignment.json     # Correction trace 2
│   ├── topology_testcases_parallelism.json   # Correction trace 3
│   └── refactored_snmp.json                  # Correction trace 4
└── correction_helper.py                       # Helper script

training-artifacts/
└── motadata_bench_corrections.jsonl          # Training data (generated)
```

---

## Quick Start (Task 1)

```bash
# 1. Start correction session
cd /home/harshil/Harshil-PoCs/RAG-Datastore
python evaluation/correction_helper.py --task refactored_code_loggers

# 2. Inside sandbox - analyze
cat README.md
cat MODEL_ATTEMPT.txt
mvn compile

# 3. Fix errors incrementally
# (Document each fix in CORRECTION_LOG.md)

# 4. Verify
bash verify.sh

# 5. Exit
exit

# 6. Save trace (when prompted)
# Choose 'yes'
```

---

## After All Corrections

```bash
# Convert traces to training data
python evaluation/convert_corrections_to_training.py

# Output: training-artifacts/motadata_bench_corrections.jsonl

# Review the training data
cat training-artifacts/motadata_bench_corrections.jsonl | jq '.'
```

---

## Success Criteria

- ✅ All 4 tasks corrected and pass verification
- ✅ Detailed correction logs for each task
- ✅ Correction traces saved to evaluation/correction_traces/
- ✅ Training data generated in motadata_bench_corrections.jsonl
- ✅ Each training example has:
  - User prompt (task description)
  - Thought process (from correction log)
  - Complete solution (all files)

---

## Next Phase

After Phase 4.1 completes:
- **Phase 4.2:** Integrate corrections into Iter10 training pipeline
- **Modify:** rag-system/prepare_iter7_data.py to load corrections (10% of dataset)
- **Train:** Iter10 on H100 (overnight run)
- **Benchmark:** Re-run motadata_bench on Iter10
- **Compare:** Iter9 (0%) vs Iter10 (target 40-60%)

---

## Troubleshooting

### Issue: Docker permission errors
```bash
# The helper script uses --user flag to avoid this
# If you still see errors, check workspace permissions
ls -la /tmp/correction_*
```

### Issue: Compilation takes too long
```bash
# Maven dependencies are cached in Docker image
# First compile may be slow (~30s), subsequent <5s
```

### Issue: Can't find MODEL_ATTEMPT.txt
```bash
# It should be in /workspace inside the container
# Check: ls /workspace
```

### Issue: Verification script fails even after fixes
```bash
# Check expected diff in task YAML
# The verifier compares against git diff from JIRA
# Your solution should match semantic intent, not exact characters
```

---

**Document Version:** 1.0  
**Last Updated:** December 18, 2025  
**Next Review:** After first task correction completes
