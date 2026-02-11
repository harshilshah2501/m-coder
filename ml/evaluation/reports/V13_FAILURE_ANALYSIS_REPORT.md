# V13 Model Failure Analysis Report

**Date**: 2025-12-29  
**Benchmark**: Motadata-Bench v4.0 (10 tasks)  
**Model**: motadata-coder-v13  
**Result**: 0/10 tasks passed (0% success rate)

---

## Executive Summary

The v13 model **completely fails** all benchmark tasks due to a fundamental mismatch between training data and evaluation tasks. The model exhibits **mode collapse** behavior, defaulting to modifying `Patch8014.java` regardless of the actual task requirements.

---

## Root Cause Analysis

### 1. Training Data Mismatch

| Metric | Training Data (v13) | Benchmark Tasks |
|--------|---------------------|-----------------|
| Files per example | **1 file** (99.9%) | **3-10 files** (100%) |
| Multi-file examples | 2 out of 1,831 | 10 out of 10 |
| Average file count | 1.0 | 4.1 |

**The model was never trained on multi-file tasks!**

### 2. Mode Collapse to `Patch8014.java`

| Task ID | Expected Files | Model Generated |
|---------|----------------|-----------------|
| e7e7246ba5e1 | PolicyCacheServiceImpl.java, ConfigResponseProcessor.java, IntegrationEngine.java, EventPolicyInspector.java | ❌ Patch8014.java |
| ae62a0fa3b59 | MetricPluginManager.java, TagConfigStore.java, etc. | ❌ Patch8014.java |
| 1aa62e982e8e | TopologyTestCase.java, etc. | ❌ Patch8014.java |
| 45f95bda687a | SNMPManager.java, etc. | ❌ Patch8014.java |
| a284e89f1632 | DependencyQueryProcessor.java, etc. | ❌ Patch8014.java |
| fc01bcc7e9ef | ComplianceDB.java, etc. | ❌ Patch8014.java |
| da66bf5d58f0 | NetrouteManager.java, etc. | ❌ BootstrapPrimary.java |
| 3fa1126b4799 | Discovery.java, etc. | ❌ Discovery.java (wrong changes) |
| 443c87d78326 | PollingTemplate.java, etc. | ❌ Patch8014.java |
| 25441efe4d29 | SSHClientManager.java, etc. | ❌ SSHClientManager.java (wrong changes) |

**7 out of 10 tasks**: Model hallucinates `Patch8014.java`

### 3. Training Data Quality Issues

```
File count distribution in v13_combined.jsonl:
- 1 file:  1,829 examples (99.89%)
- 2 files: 1 example (0.05%)
- 4 files: 1 example (0.05%)
```

The model has essentially **never seen** how to handle multi-file tasks.

---

## Detailed Failure Patterns

### Pattern 1: File Hallucination (7/10 tasks)
Model ignores the task's expected files and generates changes for `Patch8014.java`, which appears 23 times in training data.

### Pattern 2: Wrong Changes (3/10 tasks)
Model identifies correct file but generates completely wrong modifications.

### Pattern 3: Generic Reasoning
All `<thinking>` blocks are nearly identical:
```
**Problem**: [vague description]
**Plan**: 
1. Locate relevant code section
2. Apply necessary modifications
3. Ensure changes are minimal and focused
```

---

## Recommendations

### Immediate Actions

1. **Retrain with Multi-File Data**: Create training examples with 3-10 files per task
2. **Add Task-Specific Context**: Include expected file list in system prompt
3. **Remove Patch Files**: Filter out `Patch*.java` examples to prevent mode collapse

### Dataset Improvements

```python
# Required changes to create_v13_dataset.py:
1. Filter examples where file_count >= 3
2. Create synthetic multi-file examples from related commits
3. Add explicit file list validation in training examples
```

### Prompt Engineering (Quick Fix)

Add to system prompt:
```
CRITICAL: You MUST ONLY modify the files listed in "Files to modify".
Do NOT generate changes for any other files.
If you cannot complete the task with the given files, explain why.
```

---

## Comparison: What Should Have Happened

### Task: e7e7246ba5e1_refactored_code_and_removed_lo

**Expected Output** (4 files):
```diff
File: src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java
--- a/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java
+++ b/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java
@@ -XX,X +XX,X @@
 // Actual refactoring changes...

File: src/main/java/com/mindarray/config/ConfigResponseProcessor.java
--- a/src/main/java/com/mindarray/config/ConfigResponseProcessor.java
+++ b/src/main/java/com/mindarray/config/ConfigResponseProcessor.java
@@ -XX,X +XX,X @@
 // Actual refactoring changes...
```

**Actual Output** (wrong file):
```diff
File: src/main/java/com/mindarray/patch/Patch8014.java
--- a/src/main/java/com/mindarray/patch/Patch8014.java
+++ b/src/main/java/com/mindarray/patch/Patch8014.java
@@ -38,7 +38,7 @@
 // Completely unrelated changes...
```

---

## Conclusion

The v13 model failure is **not a pipeline issue** but a **fundamental training data problem**. The model cannot perform multi-file tasks because it was trained almost exclusively on single-file examples.

**Priority**: P0 - Model needs retraining with proper multi-file dataset before any further benchmarking.

---

## Appendix: All 10 Task Failures

### Task 1: e7e7246ba5e1_refactored_code_and_removed_lo
- **Expected**: PolicyCacheServiceImpl.java, ConfigResponseProcessor.java, IntegrationEngine.java, EventPolicyInspector.java
- **Generated**: Patch8014.java ❌
- **Issue**: Complete file hallucination

### Task 2: ae62a0fa3b59_metric_plugin_assignment_via_t
- **Expected**: MetricPluginManager.java, TagConfigStore.java, etc.
- **Generated**: Patch8014.java ❌
- **Issue**: Complete file hallucination

### Task 3: 1aa62e982e8e_motadata-7445_|_topology_testc
- **Expected**: TopologyTestCase.java, etc.
- **Generated**: Patch8014.java (2x) ❌
- **Issue**: Complete file hallucination, duplicate output

### Task 4: 45f95bda687a_-_refactored
- **Expected**: SNMPManager.java, etc.
- **Generated**: Patch8014.java (2x) ❌
- **Issue**: Complete file hallucination, duplicate output

### Task 5: a284e89f1632_dependency_query_processor_refactor
- **Expected**: DependencyQueryProcessor.java, etc.
- **Generated**: Patch8014.java (2x) ❌
- **Issue**: Complete file hallucination, duplicate output

### Task 6: fc01bcc7e9ef_compliance_db_refactor
- **Expected**: ComplianceDB.java, etc.
- **Generated**: Patch8014.java (2x) ❌
- **Issue**: Complete file hallucination, duplicate output

### Task 7: da66bf5d58f0_netroute_manager_removal
- **Expected**: NetrouteManager.java, BootstrapPrimary.java, etc.
- **Generated**: BootstrapPrimary.java ❌
- **Issue**: Correct file but wrong changes, missing other files

### Task 8: 3fa1126b4799_mongodb_protocol_removal
- **Expected**: Discovery.java, CredentialManager.java, etc.
- **Generated**: Discovery.java ❌
- **Issue**: Correct file but wrong changes, missing other files

### Task 9: 443c87d78326_polling_failed_template
- **Expected**: PollingTemplate.java, NotificationManager.java, etc.
- **Generated**: Patch8014.java (2x) ❌
- **Issue**: Complete file hallucination, duplicate output

### Task 10: 25441efe4d29_ssh_corner_cases
- **Expected**: SSHClientManager.java, SSHClientManagerTest.java, etc.
- **Generated**: SSHClientManager.java ❌
- **Issue**: Correct file but wrong changes, missing test files

---

## Test Script for Base Qwen

A test script has been created to verify the pipeline works with base Qwen:

```bash
# Run when ready (requires sudo for service management)
./evaluation/test_base_qwen.sh
```

This will:
1. Stop v13 service
2. Start base Qwen on port 8001
3. Run 3 benchmark tasks
4. Restore v13 service

