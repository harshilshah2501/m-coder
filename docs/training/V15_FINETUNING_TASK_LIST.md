# V15 Fine-tuning Task List

**Date**: 2025-12-31  
**Status**: Ready to commence  
**Dataset**: v15_balanced.jsonl (2,599 examples, all 7 capabilities)

---

## 📋 Task 1: Convert v15_balanced.jsonl to Search/Replace format
- **Status**: [ ] NOT_STARTED
- **Description**: Transform all 2,599 examples from unified diff format to Search/Replace blocks
- **Script**: `convert_v15_balanced_to_search_replace.py`
- **Input**: `v15_balanced.jsonl`
- **Output**: `v15_balanced_search_replace.jsonl`
- **Expected Time**: 10-15 minutes
- **Success Criteria**: All 2,599 examples converted with proper format

---

## 📋 Task 2: Validate converted dataset
- **Status**: [ ] NOT_STARTED
- **Description**: Verify all examples have proper Search/Replace format and quality
- **Checks**:
  - Format compliance (SEARCH/REPLACE blocks)
  - No duplicates
  - All 7 capabilities preserved
  - Proper structure and syntax
- **Expected Time**: 5-10 minutes
- **Success Criteria**: All validation checks pass

---

## 📋 Task 3: Retrain V15 with full balanced dataset
- **Status**: [ ] NOT_STARTED
- **Description**: Train V15 on complete 2,599 example dataset with all 7 capabilities
- **Command**: `~/Harshil-PoCs/Finetuning/venv/bin/python train_v15_balanced.py`
- **Prerequisites**:
  - [x] vLLM service stopped
  - [x] GPU memory freed
  - [x] Cleanup completed
- **Expected Time**: 4-6 hours on H100
- **Success Criteria**: Training completes without OOM, loss decreases smoothly

---

## 📋 Task 4: Test V15 comprehensive capabilities
- **Status**: [ ] NOT_STARTED
- **Description**: Verify all 7 capabilities work correctly
- **Test Categories**:
  - Tool use (balanced, not obsessed)
  - Single-file edits
  - Multi-file commits
  - Code review
  - File creation
  - Refactoring
  - Direct generation
- **Expected Time**: 2-3 hours
- **Success Criteria**: ≥85% pass rate across all capabilities

---

## ✅ Pre-Training Verification

- [x] vLLM service stopped
- [x] GPU memory freed
- [x] Cleanup completed (~500M freed)
- [x] Dataset quality verified
- [x] Training script ready
- [x] Finetuning venv verified

---

**Ready to commence fine-tuning!** 🚀

