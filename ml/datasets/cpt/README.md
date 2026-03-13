# CPT Dataset for Motadata AI Coding Assistant

**Production-ready CPT dataset for domain knowledge injection**

---

## Quick Start

```bash
# Training
python training/train_cpt.py

# Validation
python evaluation/test_cpt_model.py
```

---

## Dataset Files

- **`cpt_dataset.jsonl`** - Main training dataset (850 complete files, ~8M tokens)
- **`cpt_metadata.json`** - Statistics and file type breakdown
- **`README.md`** - This file

---

## Format

JSONL with complete files (not snippets):

```json
{"text": "complete_java_file_content"}
{"text": "complete_json_schema"}
{"text": "complete_python_script"}
```

Each line = one complete file from the Motadata repository.

---

## Contents

| File Type | Count | Purpose |
|-----------|-------|---------|
| Java | 416 | Core Motadata source code |
| JSON | 414 | Schemas, configs, API definitions |
| Python | 15 | Dataset generation tools |
| YAML | 5 | Configuration files |
| **Total** | **850** | **Complete files, ~8M tokens** |

---

## Key Principles

✅ **Complete files** - Full context with imports, headers, complete structure  
✅ **Raw format** - Code as it exists in filesystem, not curated snippets  
✅ **Multi-language** - Java, JSON, Python, YAML  
✅ **100% real code** - No synthetic data (CPT requires real domain code)  
✅ **Security-vetted** - 187 sensitive files excluded  

---

## Generation

**Script:** `datasets/tools/generate_cpt_dataset.py`

```bash
# Regenerate dataset
python3 datasets/tools/generate_cpt_dataset.py
```

**Sources:**
1. `/home/harshil/Motadata/motadata` - Production codebase
2. `/home/harshil/Harshil-PoCs/datasets` - Tools and configs

---

## Documentation

**Full documentation:** `docs/datasets/CPT_DATASET.md`

Topics covered:
- CPT vs SFT vs DPO data requirements
- Why complete files (not snippets)
- Why 100% real code (no synthetic)
- Training configuration
- Expected results
- Troubleshooting

---

## Status

✅ **Production Ready**  
✅ **Security Validated**  
✅ **Format Correct**  
✅ **Multi-Language**  
✅ **Complete Coverage**

---

**Last Updated:** January 12, 2026
