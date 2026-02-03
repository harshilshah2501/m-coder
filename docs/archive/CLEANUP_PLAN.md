# Cleanup Plan for ~/Harshil-PoCs

**Date**: 2025-12-31  
**Purpose**: Remove redundant/temporary files before V15 fine-tuning

---

## 📊 Current Disk Usage

- RAG-Datastore: 74G
- Finetuning: 18G
- Total: ~92G

---

## 🗑️ Files to Remove

### 1. Redundant Dataset Files (~340M)
- `v12_combined.jsonl` (146M) - Old V12, superseded by V15
- `v13_combined.jsonl` (81M) - Old V13, superseded by V15
- `v14_multifile.jsonl` (0 bytes) - Empty
- `v15_additional.jsonl` (32M) - Intermediate, merged
- `v15_balanced_with_duplicates.jsonl` (60M) - Duplicate version
- `v15_missing_capabilities.jsonl` (3.6M) - Intermediate
- `v15_search_replace.jsonl` (3.0M) - Old conversion
- `motadata_finetuning_data.jsonl` (15M) - Old test data

### 2. Training Logs (~50M)
- `training_v*.log` - Old/failed training logs
- `merge_*.log` - Old merge logs
- `deploy_*.log` - Old deployment logs

### 3. Test Files (~5M)
- `test_*.py` - Test scripts
- `*test_results.json` - Old test results

### 4. Archive Directory (~100M)
- `archive_20251229/` - Old archived files

---

## ✅ Files to Keep

- `v15_balanced.jsonl` (61M) - **MAIN TRAINING FILE**
- `v15_balanced_search_replace.jsonl` (8.8M) - Converted format
- `v14_multifile_final.jsonl` (2.7M) - V14 baseline
- All training/validation scripts
- All documentation (.md files)

---

**Expected Cleanup**: ~500M freed

