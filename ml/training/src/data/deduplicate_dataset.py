#!/usr/bin/env python3
"""
Deduplicate V17 dataset - remove duplicate questions
Keep only unique, high-quality examples
"""

import json
from pathlib import Path
from datetime import datetime

print("="*80)
print("DEDUPLICATING V17 DATASET")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

INPUT_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v17_motadata_examples.jsonl")
OUTPUT_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v17_motadata_examples_dedup.jsonl")

print("STEP 1: Loading Dataset")
print("-" * 80)

examples = []
with open(INPUT_FILE, 'r') as f:
    for line in f:
        examples.append(json.loads(line))

print(f"✓ Loaded {len(examples)} examples")

print("\nSTEP 2: Identifying Duplicates")
print("-" * 80)

seen_questions = {}
duplicates = []
unique_examples = []

for idx, example in enumerate(examples):
    question = example.get("question", "")
    
    if question in seen_questions:
        duplicates.append({
            "question": question,
            "first_occurrence": seen_questions[question],
            "duplicate_at": idx
        })
    else:
        seen_questions[question] = idx
        unique_examples.append(example)

print(f"✓ Found {len(duplicates)} duplicate questions")
print(f"✓ Unique examples: {len(unique_examples)}")

print("\nSTEP 3: Duplicate Analysis")
print("-" * 80)

if duplicates:
    print(f"Sample duplicates (first 5):")
    for dup in duplicates[:5]:
        print(f"  - Question: {dup['question'][:60]}...")
        print(f"    First at index {dup['first_occurrence']}, duplicate at {dup['duplicate_at']}")

print("\nSTEP 4: Saving Deduplicated Dataset")
print("-" * 80)

with open(OUTPUT_FILE, 'w') as f:
    for example in unique_examples:
        f.write(json.dumps(example) + '\n')

print(f"✓ Saved {len(unique_examples)} unique examples")
print(f"✓ File: {OUTPUT_FILE.name}")
print(f"✓ File size: {OUTPUT_FILE.stat().st_size / (1024*1024):.1f} MB")

print("\nSTEP 5: Summary")
print("-" * 80)

print(f"Original examples: {len(examples)}")
print(f"Duplicates removed: {len(duplicates)}")
print(f"Final unique examples: {len(unique_examples)}")
print(f"Deduplication rate: {(len(duplicates)/len(examples)*100):.1f}%")

print("\n" + "="*80)
print("DEDUPLICATION COMPLETE")
print("="*80)
print(f"✓ {len(unique_examples):,} unique real Motadata examples")
print(f"✓ Ready for V17 training")
print("="*80)

