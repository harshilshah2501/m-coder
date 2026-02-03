#!/usr/bin/env python3
"""
Create train/val/test splits for V16.1 dataset
80% train / 10% val / 10% test
"""

import json
import random
from pathlib import Path
from datetime import datetime

print("="*80)
print("V16.1 DATASET SPLITS CREATION")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

# Paths
DATASET_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_surgical.jsonl")
OUTPUT_DIR = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_splits")
OUTPUT_DIR.mkdir(exist_ok=True)

# Split ratios
TRAIN_RATIO = 0.8
VAL_RATIO = 0.1
TEST_RATIO = 0.1

print("STEP 1: Loading Dataset")
print("-" * 80)

examples = []
with open(DATASET_FILE, 'r') as f:
    for line in f:
        try:
            examples.append(json.loads(line))
        except:
            pass

print(f"✓ Loaded {len(examples):,} examples from v16_1_surgical.jsonl")

print("\nSTEP 2: Shuffling Dataset")
print("-" * 80)

# Set seed for reproducibility
random.seed(42)
random.shuffle(examples)
print(f"✓ Shuffled {len(examples):,} examples (seed=42)")

print("\nSTEP 3: Creating Splits")
print("-" * 80)

total = len(examples)
train_size = int(total * TRAIN_RATIO)
val_size = int(total * VAL_RATIO)
test_size = total - train_size - val_size

train_examples = examples[:train_size]
val_examples = examples[train_size:train_size + val_size]
test_examples = examples[train_size + val_size:]

print(f"Train: {len(train_examples):,} examples ({len(train_examples)/total*100:.1f}%)")
print(f"Val:   {len(val_examples):,} examples ({len(val_examples)/total*100:.1f}%)")
print(f"Test:  {len(test_examples):,} examples ({len(test_examples)/total*100:.1f}%)")
print(f"Total: {len(train_examples) + len(val_examples) + len(test_examples):,} examples")

print("\nSTEP 4: Saving Splits")
print("-" * 80)

# Save train
train_file = OUTPUT_DIR / "train.jsonl"
with open(train_file, 'w') as f:
    for example in train_examples:
        f.write(json.dumps(example) + '\n')
print(f"✓ Saved {len(train_examples):,} examples to train.jsonl")

# Save val
val_file = OUTPUT_DIR / "val.jsonl"
with open(val_file, 'w') as f:
    for example in val_examples:
        f.write(json.dumps(example) + '\n')
print(f"✓ Saved {len(val_examples):,} examples to val.jsonl")

# Save test
test_file = OUTPUT_DIR / "test.jsonl"
with open(test_file, 'w') as f:
    for example in test_examples:
        f.write(json.dumps(example) + '\n')
print(f"✓ Saved {len(test_examples):,} examples to test.jsonl")

print("\nSTEP 5: Verification")
print("-" * 80)

# Verify file sizes
train_mb = train_file.stat().st_size / (1024*1024)
val_mb = val_file.stat().st_size / (1024*1024)
test_mb = test_file.stat().st_size / (1024*1024)
total_mb = train_mb + val_mb + test_mb

print(f"Train: {train_mb:.1f} MB")
print(f"Val:   {val_mb:.1f} MB")
print(f"Test:  {test_mb:.1f} MB")
print(f"Total: {total_mb:.1f} MB")

print("\nSTEP 6: Summary")
print("-" * 80)

summary = {
    "dataset": "v16_1_surgical",
    "total_examples": total,
    "splits": {
        "train": {
            "count": len(train_examples),
            "percentage": round(len(train_examples)/total*100, 2),
            "file": str(train_file),
            "size_mb": round(train_mb, 2)
        },
        "val": {
            "count": len(val_examples),
            "percentage": round(len(val_examples)/total*100, 2),
            "file": str(val_file),
            "size_mb": round(val_mb, 2)
        },
        "test": {
            "count": len(test_examples),
            "percentage": round(len(test_examples)/total*100, 2),
            "file": str(test_file),
            "size_mb": round(test_mb, 2)
        }
    },
    "seed": 42,
    "created": datetime.now().isoformat()
}

summary_file = OUTPUT_DIR / "split_summary.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"✓ Saved split summary to split_summary.json")

print("\n" + "="*80)
print("V16.1 SPLITS CREATION COMPLETE")
print("="*80)
print(f"✓ Train: {len(train_examples):,} examples")
print(f"✓ Val:   {len(val_examples):,} examples")
print(f"✓ Test:  {len(test_examples):,} examples")
print(f"✓ Location: {OUTPUT_DIR}")
print("="*80)

