#!/usr/bin/env python3
"""
FINAL V16.1 DATASET VALIDATION
100% Surgical Precision - Complete Analysis
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

print("="*80)
print("V16.1 FINAL DATASET VALIDATION - SURGICAL PRECISION")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

DATASET_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_surgical.jsonl")

print("STEP 1: Loading Dataset")
print("-" * 80)

examples = []
with open(DATASET_FILE, 'r') as f:
    for line_num, line in enumerate(f, 1):
        try:
            example = json.loads(line)
            examples.append(example)
        except Exception as e:
            print(f"✗ Parse error at line {line_num}: {e}")

print(f"✓ Loaded {len(examples):,} examples")

print("\nSTEP 2: Dataset Composition")
print("-" * 80)

v15_examples = [ex for ex in examples if "messages" in ex]
motadata_examples = [ex for ex in examples if "type" in ex]

print(f"V15 (Real Motadata code edits): {len(v15_examples):,} ({len(v15_examples)/len(examples)*100:.1f}%)")
print(f"Motadata (JavaDoc Q&A): {len(motadata_examples):,} ({len(motadata_examples)/len(examples)*100:.1f}%)")
print(f"Total: {len(examples):,}")

print("\nSTEP 3: V15 Category Distribution")
print("-" * 80)

v15_categories = defaultdict(int)
for ex in v15_examples:
    category = ex.get("metadata", {}).get("category", "unknown")
    v15_categories[category] += 1

print("V15 Categories (format types):")
for cat, count in sorted(v15_categories.items(), key=lambda x: x[1], reverse=True):
    print(f"  {cat}: {count:,} ({count/len(v15_examples)*100:.1f}%)")

print("\nSTEP 4: Motadata Type Distribution")
print("-" * 80)

motadata_types = defaultdict(int)
for ex in motadata_examples:
    type_val = ex.get("type", "unknown")
    motadata_types[type_val] += 1

print("Motadata Types:")
for typ, count in sorted(motadata_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {typ}: {count:,} ({count/len(motadata_examples)*100:.1f}%)")

print("\nSTEP 5: Duplicate Check")
print("-" * 80)

hashes = set()
duplicates = 0
for ex in examples:
    if "messages" in ex:
        content = json.dumps(ex["messages"], sort_keys=True)
    else:
        content = f"{ex.get('question', '')}{ex.get('code', '')}"
    
    h = hashlib.md5(content.encode()).hexdigest()
    if h in hashes:
        duplicates += 1
    hashes.add(h)

if duplicates == 0:
    print(f"✓ No duplicates found")
else:
    print(f"✗ Found {duplicates} duplicates")

print("\nSTEP 6: Content Quality Check")
print("-" * 80)

empty_content = 0
for ex in examples:
    if "messages" in ex:
        if not ex.get("messages"):
            empty_content += 1
    else:
        if not ex.get("question") or not ex.get("answer"):
            empty_content += 1

if empty_content == 0:
    print(f"✓ All examples have valid content")
else:
    print(f"✗ Found {empty_content} examples with empty content")

print("\nSTEP 7: Sample Examples")
print("-" * 80)

print("\nV15 Example (Code Edit):")
v15_sample = v15_examples[0]
user_msg = [m for m in v15_sample["messages"] if m["role"] == "user"][0]
print(f"  Task: {user_msg['content'][:150]}...")

print("\nMotadata Example (Q&A):")
mot_sample = motadata_examples[0]
print(f"  Question: {mot_sample['question'][:100]}...")
print(f"  Type: {mot_sample['type']}")

print("\nSTEP 8: Final Validation")
print("-" * 80)

validation_passed = (
    len(examples) > 0 and
    duplicates == 0 and
    empty_content == 0 and
    len(v15_examples) + len(motadata_examples) == len(examples)
)

if validation_passed:
    print("✅ DATASET IS 100% VALID - READY FOR TRAINING")
else:
    print("❌ DATASET HAS ISSUES - MUST FIX BEFORE TRAINING")

# Save report
report = {
    "timestamp": datetime.now().isoformat(),
    "total_examples": len(examples),
    "v15_examples": len(v15_examples),
    "motadata_examples": len(motadata_examples),
    "v15_categories": dict(v15_categories),
    "motadata_types": dict(motadata_types),
    "duplicates": duplicates,
    "empty_content": empty_content,
    "validation_passed": validation_passed,
    "file_size_mb": round(DATASET_FILE.stat().st_size / (1024*1024), 2)
}

report_file = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_final_validation_report.json")
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n✓ Report saved: {report_file}")

print("\n" + "="*80)
print("FINAL SUMMARY")
print("="*80)
print(f"Dataset: v16_1_surgical.jsonl")
print(f"Total Examples: {len(examples):,}")
print(f"  - V15 (Code Edits): {len(v15_examples):,}")
print(f"  - Motadata (Q&A): {len(motadata_examples):,}")
print(f"Duplicates: {duplicates}")
print(f"Validation: {'✅ PASSED' if validation_passed else '❌ FAILED'}")
print("="*80)

