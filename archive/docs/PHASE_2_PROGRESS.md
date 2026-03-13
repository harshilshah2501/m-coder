# Phase 2 Progress Report: Dataset Preparation for Iteration 8

**Date:** December 16, 2025  
**Status:** In Progress - 40% Complete  

---

## ✅ Completed Tasks

### 1. Dataset Validation (100%)
**Tool:** `validate_dataset.py`

**Findings:**
- **Total Examples:** 12,386
  - Tool-Based (Agentic): 11,485 (92.7%)
  - Direct Answer: 901 (7.3%)
- **Critical Issues:**
  - ❌ 11,485 examples contain "ChromaDB" references
  - ❌ 11,485 examples missing mode indicators
  - ⚠️ Severe imbalance: 93% agentic, 7% direct

**Severity:** 🔴 CRITICAL

---

### 2. Dataset C Cleaning (100%)
**Tool:** `clean_dataset_c.py`

**Actions Taken:**
- ✅ Replaced "ChromaDB" → "Qdrant" in 11,485 examples
- ✅ Added "You are an agent. Use the provided tools..." to system prompts
- ✅ Validated tool schemas match current RAG API

**Output:** `iter7_training_data_cleaned.jsonl` (12,386 examples)

---

### 3. Dataset D Generation - Pilot (20%)
**Tool:** `generate_dataset_d_direct.py`

**Pilot Results (50-example test run):**
- ✅ Generated: 50 valid examples
- ⚠️ Skipped: 49 examples (50% skip rate)
- ❌ **Quality Issue:** Model still outputting tool-like reasoning even in CHAT mode
  - Example: "Why did I select this file? I ran the query..."
  - Root Cause: Iter 7 is too heavily tool-trained to generate clean direct answers

**Verdict:** Generator works but current model is not suitable for self-generation.

---

## 🚧 Blocked / In Progress

### Dataset D Generation Blocker

**Problem:** The Iter 7 model cannot generate clean direct answers because it's over-trained on agentic behavior.

**Options:**
1. **Manual Curation** (Slow, High Quality)
   - Write 500 golden examples by hand
   - Use templates to expand to 2,500
   - **Effort:** ~16 hours
   
2. **Use Base Model** (Fast, Medium Quality)
   - Use `Qwen2.5-Coder-7B-Instruct` (pre-finetuning) to generate examples
   - It doesn't have tool obsession
   - **Effort:** ~2 hours
   
3. **Hybrid Approach** (Recommended)
   - Manually curate 200 golden examples across all categories
   - Use base model to generate 2,300 variations
   - **Effort:** ~6 hours

---

## 📊 Current Dataset Inventory

| Dataset | Examples | Type | Status | Issues |
|---------|----------|------|--------|--------|
| **Dataset A (Jira)** | 691 | Direct | ✅ Ready | None |
| **Dataset B (Multi-file)** | 210 | Direct | ✅ Ready | None |
| **Dataset C (Cleaned)** | 11,485 | Agentic | ✅ Ready | ChromaDB fixed |
| **Dataset D (Direct)** | 0 / 2,500 | Direct | 🔴 Blocked | Generator needs base model |
| **Dataset D (Agentic)** | 0 / 2,500 | Agentic | ⏳ Waiting | Depends on D-Direct |

**Total Current:** 12,386 examples  
**Target for Iter 8:** 17,386 examples

---

## 🎯 Recommended Next Steps

### Option A: Quick Path (Use Base Model)
**Timeline:** 1-2 days

1. Load `Qwen2.5-Coder-7B-Instruct` (base model, no finetuning)
2. Generate 2,500 direct examples using `generate_dataset_d_direct.py`
3. Manually review 10% (250 examples) for quality
4. Generate 2,500 agentic examples with corrected Qdrant schemas
5. Merge all datasets → Create `iter8_training_data.jsonl`
6. Split 95/5 → Begin Iter 8 training

**Pros:**
- Fast (2 days total)
- Base model won't have tool obsession

**Cons:**
- May lack Motadata-specific knowledge
- Requires manual review

---

### Option B: High Quality Path (Manual + Templates)
**Timeline:** 5-7 days

1. Manually write 500 golden examples:
   - 100 Knowledge (AbstractConfigStore, EventBus, etc.)
   - 100 Architecture (Discovery flow, Monitoring, etc.)
   - 100 Code Review
   - 100 Debugging (RCA)
   - 100 Reasoning (Memory leaks, complexity analysis)
2. Create templates from golden examples
3. Use templates to generate 2,000 variations
4. Proceed with agentic generation + merge

**Pros:**
- Highest quality
- Perfect Motadata domain alignment

**Cons:**
- Slow (1 week)
- Labor-intensive

---

### Option C: Hybrid (Recommended)
**Timeline:** 3-4 days

1. **Day 1:** Manually write 200 golden examples (40/category)
2. **Day 2:** Use base model + templates to generate 2,300 examples
3. **Day 3:** Generate 2,500 agentic examples, merge datasets
4. **Day 4:** Begin Iter 8 training

**Balance:** Speed + Quality

---

## 🔧 Tools Created

| Tool | Purpose | Status |
|------|---------|--------|
| `validate_dataset.py` | Scan for ChromaDB, tool issues | ✅ Complete |
| `clean_dataset_c.py` | Fix Dataset C (Qdrant migration) | ✅ Complete |
| `generate_dataset_d_direct.py` | Self-generate direct examples | ⚠️ Works but model unsuitable |

---

## 📋 Decision Required

**Question:** Which path should we take for Dataset D generation?

- [ ] **Option A:** Use base model (fast, 2 days)
- [ ] **Option B:** Manual curation (slow, 7 days)
- [x] **Option C:** Hybrid approach (recommended, 3-4 days)

Once decided, I can proceed with execution.

---

**Prepared by:** GitHub Copilot  
**Next Review:** After Dataset D completion
