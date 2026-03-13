# V16.1 Model - Comprehensive KPI Evaluation Plan

**Date:** 2026-01-07  
**Model:** v16.1 (Qwen2.5-Coder-14B-Instruct + LoRA Merged)  
**Framework:** Based on `docs/evaluation/LLM-IDE-KPI-Framework-Objective.md`  
**Status:** PLANNING PHASE

---

## Executive Summary

This document outlines the comprehensive KPI evaluation plan for the V16.1 fine-tuned model. The basic STEP 5 testing (10 samples) has been completed successfully. This plan defines the **full evaluation** required before production deployment.

---

## Current Status: STEP 5 Basic Testing

✅ **Completed:**
- 10 validation samples tested
- Average inference time: 11.55s
- 100% completion rate (no truncation)
- Proper SEARCH/REPLACE format generation

⚠️ **Limitations:**
- Small sample size (10 vs 391 validation samples)
- No KPI framework compliance testing
- No IDE plugin integration testing
- No tool use evaluation

---

## KPI Evaluation Framework

### KPI 1: Project Indexing Correctness (Target: ≥90%)

**Status:** ⚠️ **BLOCKED** - Requires IDE plugin integration

**Dependencies:**
- IntelliJ IDEA plugin with indexing capability
- Continue.dev or custom plugin integration
- Motadata codebase indexed

**Test Plan:**
1. Index Motadata codebase (25-30 test classes)
2. Run 50 file discovery queries
3. Measure accuracy: (Files_Found / Expected_Files) × 100
4. Track false positives (max ≤10%)
5. Measure latency P95 (<800ms target)

**Test Cases:**
- API Discovery: "Show me CorrectionProfile API" → 4-6 files
- EventBus Handler: "Find EVENT_DISCOVERY handlers" → 8-12 files
- Config Search: "Where is database config?" → 3-5 files
- Multi-Module: "ConfigDB → Datastore" → Classes across modules
- Circular Dependencies: "Trace ConfigStore → Bootstrap" → 5-7 files

**Estimated Time:** 4-6 hours (after IDE plugin setup)

**Deliverable:** `kpi1_indexing_results.json`

---

### KPI 2: Output Truncation Prevention (Target: ≥99%)

**Status:** ⚠️ **PARTIALLY TESTED** - Need 100 samples

**Current Results:**
- ✅ 10/10 samples complete (100%)
- ✅ No truncation markers found
- ⚠️ Sample size too small for statistical significance

**Test Plan:**
1. Run inference on 100 validation samples
2. Check for truncation markers in last 100 chars
3. Validate bracket/brace matching for code
4. Verify diff headers present (for patches)
5. Confirm token count <95% of max_tokens

**Test Script:** `training/evaluation/test_truncation_kpi2.py`

**Acceptance Criteria:**
- ✅ ≥99% complete responses (≤1 truncation per 100)
- ✅ 100% bracket/quote matching
- ✅ Token budget <95%

**Estimated Time:** 2-3 hours

**Deliverable:** `kpi2_truncation_results.json`

---

### KPI 3: System Prompt & Dataset Coverage (Target: 100% use-cases)

**Status:** ⚠️ **PARTIALLY TESTED** - Need systematic use-case testing

**Current Results:**
- ✅ Q&A: 3 samples tested
- ✅ SEARCH/REPLACE (Single): 4 samples tested
- ✅ Code Review: 2 samples tested
- ✅ Refactoring (Multi-file): 1 sample tested
- ❌ Debugging/RCA: Not tested
- ❌ Multi-file awareness: Not validated

**Test Plan:**

#### 3.1 Use-Case Coverage Matrix

| Use-Case | Samples | Expected Behavior | Pass Criteria |
|----------|---------|-------------------|---------------|
| **Q&A / Knowledge** | 20 | Answer from context, cite code | ≥95% accurate |
| **Code Gen (Single)** | 20 | Complete class, compiles | ≥95% valid |
| **Code Gen (Multi-File)** | 20 | ≥3 files, valid diffs | ≥90% multi-aware |
| **Debugging / RCA** | 20 | Identifies handler, suggests fix | ≥85% correct |
| **Code Review** | 20 | Points out violations, cites patterns | ≥80% useful |

#### 3.2 Information Layer Richness

Calculate richness score:
```
richness_score = (
    (files_indexed / 10) * 0.10 +
    (entities_extracted / 5) * 0.10 +
    (rag_chunks / 5) * 0.30 +
    (system_prompt_present) * 0.20 +
    (examples_included / 2) * 0.30
)
```

**Target:** ≥0.75

#### 3.3 Post-Processing Validation

Test all 6 stages:
1. Token cleanup (no special tokens)
2. Format validation (valid Java/diff)
3. Syntax correction (brackets match)
4. Security checks (no exec(), secrets)
5. Context injection (imports added)
6. Display formatting (renders correctly)

**Test Script:** `training/evaluation/test_coverage_kpi3.py`

**Estimated Time:** 4-6 hours

**Deliverable:** `kpi3_coverage_results.json`

---

### KPI 4: Tool Use & Function Calling (Target: ≥90%)

**Status:** ❌ **NOT APPLICABLE** - Current model doesn't use tools

**Reason:** The V16.1 model is trained for direct SEARCH/REPLACE generation, not tool-based workflows.

**Future Consideration:**
- If deploying with IDE plugin that supports tool calling
- If integrating with Continue.dev function calling
- If adding RAG retrieval as a "tool"

**Estimated Time:** N/A (blocked until tool integration)

**Deliverable:** N/A

---

## Recommended Evaluation Sequence

### Phase 1: Immediate Testing (Can Start Now)

**Priority 1: KPI 2 - Truncation Testing** (2-3 hours)
- ✅ No dependencies
- ✅ Can run immediately
- ✅ High value for production readiness

**Priority 2: KPI 3 - Use-Case Coverage** (4-6 hours)
- ✅ No dependencies
- ✅ Can run immediately
- ✅ Validates training effectiveness

### Phase 2: Post-Deployment Testing (After STEP 6)

**Priority 3: Full Validation Set** (8-12 hours)
- Run on all 391 validation samples
- Calculate accuracy vs ground truth
- Generate comprehensive metrics

**Priority 4: KPI 1 - Indexing** (After IDE plugin)
- Requires vLLM deployment
- Requires IDE plugin integration
- Real-world testing

---

## Implementation Scripts

### Script 1: KPI 2 - Truncation Testing
**File:** `training/evaluation/test_truncation_kpi2.py`
**Purpose:** Test 100 samples for truncation, bracket matching, token budget
**Runtime:** ~30-40 minutes (100 samples × ~20s avg)

### Script 2: KPI 3 - Use-Case Coverage
**File:** `training/evaluation/test_coverage_kpi3.py`
**Purpose:** Test 100 samples across 5 use-cases (20 each)
**Runtime:** ~30-40 minutes

### Script 3: Full Validation Evaluation
**File:** `training/evaluation/test_full_validation.py`
**Purpose:** Run all 391 validation samples, calculate metrics
**Runtime:** ~2-3 hours (391 samples × ~20s avg)

---

## Success Criteria

### Minimum Shipping Thresholds

| KPI | Target | Current | Status | Action |
|-----|--------|---------|--------|--------|
| **KPI 1: Indexing** | ≥90% | N/A | ⏸️ BLOCKED | Deploy to vLLM first |
| **KPI 2: Truncation** | ≥99% | 100% (n=10) | ⚠️ EXPAND | Test 100 samples |
| **KPI 3: Coverage** | 100% | 80% (partial) | ⚠️ EXPAND | Test all use-cases |
| **KPI 4: Tool Use** | ≥90% | N/A | ⏸️ N/A | Not applicable |

### Go/No-Go Decision

**SHIP if:**
- ✅ KPI 2: ≥99% (100 samples)
- ✅ KPI 3: All 5 use-cases ≥80%
- ✅ No critical failures in validation set

**HOLD if:**
- ❌ KPI 2: <99% (truncation issues)
- ❌ KPI 3: Any use-case <70%
- ❌ Critical failures (hallucination, security)

---

## Next Steps

**Immediate Actions:**
1. ✅ Create evaluation scripts (KPI 2, KPI 3)
2. ⏳ Run KPI 2 truncation testing (100 samples)
3. ⏳ Run KPI 3 use-case coverage (100 samples)
4. ⏳ Analyze results and generate report

**Post-STEP 6 Actions:**
5. ⏳ Deploy to vLLM
6. ⏳ Run full validation set (391 samples)
7. ⏳ Integrate with IDE plugin
8. ⏳ Run KPI 1 indexing tests

---

**Created:** 2026-01-07T05:50:00  
**Author:** Augment Agent  
**Status:** READY FOR IMPLEMENTATION

