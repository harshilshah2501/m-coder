# V17 DPO Dataset Summary

**Date:** 2026-01-09  
**Status:** ✅ Complete and validated

## Overview

Generated a **spec-compliant DPO preference dataset** for training v17 (DeepSeek-inspired DPO on Qwen2.5-Coder-14B) following your documented dataset specification standards.

## Outputs

### 1. Generated Pairs
- **File:** `datasets/v17_dpo_pairs.jsonl`
- **Count:** 275 pairs
- **Size:** 0.2 MB
- **Format:** ChatML (OpenAI messages format per spec)

### 2. Train/Val/Test Splits
- **Train:** `v17_dpo_pairs_train.jsonl` (220 pairs, 80%)
- **Val:** `v17_dpo_pairs_val.jsonl` (27 pairs, 9.8%)
- **Test:** `v17_dpo_pairs_test.jsonl` (28 pairs, 10.2%)
- **Stratified by category** to maintain distribution

### 3. Validation Report
- **File:** `datasets/v17_dpo_validation_report.json`
- **All 7 gates passed** (100% compliance)

### 4. Metadata
- **File:** `datasets/v17_dpo_metadata.json`
- Includes split statistics, source distribution, difficulty breakdown

## Quality Assurance - All 7 Validation Gates Passed

| Gate | Check | Result |
|------|-------|--------|
| **1** | JSON Validity | ✅ 275/275 valid |
| **2** | Format Consistency | ✅ 0 errors, per-category schemas uniform |
| **3** | Field Presence | ✅ 100% (messages, category, metadata) |
| **4** | Duplicate Detection | ✅ 0 duplicates (MD5 hashing) |
| **5** | Content Quality | ✅ 275/275 valid (min length checks) |
| **6** | Token Distribution | ✅ mean=56, median=59, p95=65, max=65 |
| **7** | Motadata Alignment | ✅ All pairs use Motadata patterns, no warnings |

## Dataset Composition

### By Category (per spec)
- **single_file** (SEARCH-REPLACE edits): 225 pairs (81.8%)
- **file_creation** (PLAIN CODE): 50 pairs (18.2%)

### By Source
- **synthetic_search_replace:** 80 pairs (validation + refactoring scenarios)
- **synthetic_plain_code:** 50 pairs (new class/file creation)
- **synthetic_bugfix:** 70 pairs (NPE fixes, null safety)
- **synthetic_context_usage:** 75 pairs (RAG-aware implementations)

### By Difficulty
- **beginner:** 130 pairs (47.3%) – validation, basic patterns
- **intermediate:** 145 pairs (52.7%) – context usage, bugfixes

## Format Compliance

### ChatML Messages Structure
Each pair contains:
```json
{
  "messages": [
    {"role": "user", "content": "...prompt..."},
    {"role": "assistant", "content": "...chosen code..."}
  ],
  "category": "single_file|file_creation",
  "difficulty": "beginner|intermediate",
  "tags": ["tag1", "tag2"],
  "task_id": "...",
  "source": "synthetic_*",
  "metadata": {...}
}
```

### Code Format Examples
**SEARCH-REPLACE:**
```
File: path/to/file.java
<<<< SEARCH
[old code]
====
[new code]
>>>> REPLACE
```

**PLAIN CODE:**
```
File: path/to/NewClass.java
```java
[complete file content]
```
```

## Training Readiness

✅ **Format:** ChatML with spec-compliant structure  
✅ **Validation:** All 7 gates passed  
✅ **Size:** 220 training pairs sufficient for DPO on ~14B model  
✅ **Balance:** Stratified splits maintain category distribution  
✅ **Metadata:** Rich tagging (categories, difficulty, source, tags)  
✅ **Tested:** Load validation confirms TRL compatibility  

## Next Steps

### Immediate
1. Launch DPO training: `python training/src/finetuning/train_v17_dpo.py`
2. Monitor loss curves (should decrease, KL stay ~0.2)
3. Run evaluation on v17_dpo_pairs_test.jsonl after training

### Post-DPO
1. Merge LoRA adapters into v17_dpo model
2. Run comprehensive evaluation (compile success, instruction-following, context usage)
3. Compare v17_dpo vs v16_1 on HumanEval, MultiPL-E, custom benchmarks

### Optional Enhancements
- Add real evaluation failures to dataset (currently 100% synthetic)
- Expand context-usage pairs with actual RAG snippets
- Implement GRPO variant (group preference) for larger scale

## Files Modified/Created

### New Files
- `datasets/generation/generate_dpo_pairs_v2.py` – Spec-compliant pair generator
- `datasets/generation/create_splits.py` – Train/val/test split script
- `training/src/validation/validate_dpo_dataset.py` – Format validation
- `datasets/v17_dpo_pairs.jsonl` – Full dataset
- `datasets/v17_dpo_pairs_train.jsonl` – Training split
- `datasets/v17_dpo_pairs_val.jsonl` – Validation split
- `datasets/v17_dpo_pairs_test.jsonl` – Test split
- `datasets/v17_dpo_metadata.json` – Metadata and stats
- `datasets/v17_dpo_validation_report.json` – Validation gate results

### Modified Files
- `training/src/finetuning/train_v17_dpo.py` – Updated to use train/val splits

## Specification Alignment

✅ Follows the **V15 Gold Dataset Specification** principles:
- Valid JSON with no parse errors
- Consistent per-category format (SEARCH-REPLACE vs PLAIN CODE)
- Proper metadata fields (category, difficulty, tags, source)
- Motadata codebase alignment (package names, class patterns)
- Token distribution within expected ranges
- Stratified train/val/test splits (80/10/10)
- Zero duplicates (MD5-based detection)
- Content quality checks (minimum length, non-empty fields)

---

**Status:** Ready for DPO training  
**Estimated training time:** 1–2 hours on H100  
**Expected outcome:** Improved instruction-following, reduced hallucination
