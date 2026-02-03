#!/usr/bin/env python3
"""
Create V16.1 (Upgraded) Dataset
Merge V15 base with V17 real Motadata samples
Maintain V16 structure + add real code examples
"""

import json
import random
from pathlib import Path
from datetime import datetime
from collections import defaultdict

print("="*80)
print("CREATING V16.1 UPGRADED DATASET")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

V15_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v15_gold.jsonl")
V17_MOTADATA_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v17_motadata_examples_dedup.jsonl")
OUTPUT_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_upgraded.jsonl")

print("STEP 1: Loading Datasets")
print("-" * 80)

v15_examples = []
v17_examples = []

# Load V15
with open(V15_FILE, 'r') as f:
    for line in f:
        try:
            v15_examples.append(json.loads(line))
        except:
            pass

print(f"✓ V15 base: {len(v15_examples):,} examples")

# Load V17 Motadata
with open(V17_MOTADATA_FILE, 'r') as f:
    for line in f:
        try:
            v17_examples.append(json.loads(line))
        except:
            pass

print(f"✓ V17 Motadata: {len(v17_examples):,} examples")

print("\nSTEP 2: Categorize V17 Examples")
print("-" * 80)

v17_by_type = defaultdict(list)
for ex in v17_examples:
    ex_type = ex.get("type", "unknown")
    v17_by_type[ex_type].append(ex)

print("V17 Motadata breakdown:")
for ex_type, exs in v17_by_type.items():
    print(f"  {ex_type}: {len(exs):,}")

print("\nSTEP 3: Merge Datasets")
print("-" * 80)

merged = v15_examples + v17_examples
print(f"✓ Merged total: {len(merged):,} examples")
print(f"  V15: {len(v15_examples):,}")
print(f"  V17 Motadata: {len(v17_examples):,}")

print("\nSTEP 4: Analyze Merged Distribution")
print("-" * 80)

merged_types = defaultdict(int)
merged_difficulty = defaultdict(int)

for ex in merged:
    ex_type = ex.get("type", "unknown")
    difficulty = ex.get("difficulty", "unknown")
    merged_types[ex_type] += 1
    merged_difficulty[difficulty] += 1

print("Merged type distribution:")
for ex_type, count in sorted(merged_types.items(), key=lambda x: x[1], reverse=True):
    pct = (count / len(merged)) * 100
    print(f"  {ex_type}: {count:,} ({pct:.1f}%)")

print("\nMerged difficulty distribution:")
for difficulty, count in sorted(merged_difficulty.items(), key=lambda x: x[1], reverse=True):
    pct = (count / len(merged)) * 100
    print(f"  {difficulty}: {count:,} ({pct:.1f}%)")

print("\nSTEP 5: Shuffle and Save")
print("-" * 80)

random.shuffle(merged)

with open(OUTPUT_FILE, 'w') as f:
    for example in merged:
        f.write(json.dumps(example) + '\n')

print(f"✓ Saved {len(merged):,} examples to v16_1_upgraded.jsonl")
print(f"✓ File size: {OUTPUT_FILE.stat().st_size / (1024*1024):.1f} MB")

print("\nSTEP 6: Summary")
print("-" * 80)

print(f"\nV16.1 UPGRADED DATASET STATISTICS:")
print(f"  Total examples: {len(merged):,}")
print(f"  Growth from V15: +{len(v17_examples):,} (+{(len(v17_examples)/len(v15_examples)*100):.1f}%)")
print(f"  Real Motadata examples: {len(v17_examples):,} ({(len(v17_examples)/len(merged)*100):.1f}%)")

print("\n" + "="*80)
print("V16.1 UPGRADE COMPLETE")
print("="*80)
print(f"✓ Dataset: v16_1_upgraded.jsonl")
print(f"✓ Total: {len(merged):,} examples")
print(f"✓ Includes real Motadata code")
print("="*80)

