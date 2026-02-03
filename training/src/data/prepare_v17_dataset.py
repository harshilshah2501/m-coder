#!/usr/bin/env python3
"""
PHASE 2: V17 TRAINING DATASET PREPARATION
Focus: Enhanced Q&A capabilities with code context

Dataset composition:
- 40% Q&A pairs (code understanding + explanation)
- 30% Code generation (with context)
- 20% Code refactoring (before/after)
- 10% Bug fixing (problem/solution)
"""

import json
import os
import random
from datetime import datetime
from pathlib import Path

print("="*80)
print("PHASE 2: V17 TRAINING DATASET PREPARATION")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

# Dataset paths
DATASET_DIR = Path("/home/harshil/Harshil-PoCs/datasets")
V15_GOLD = DATASET_DIR / "v15_gold.jsonl"
V15_ENHANCED = DATASET_DIR / "v15_enhanced.jsonl"
V17_DATASET_FILE = DATASET_DIR / "v17_training_data.jsonl"
V17_STATS_FILE = DATASET_DIR / "v17_dataset_stats.json"

print("STEP 1: Analyzing Existing V15 Datasets")
print("-" * 80)

# Check existing datasets
existing_files = list(DATASET_DIR.glob("*.jsonl"))
print(f"Found {len(existing_files)} existing dataset files:")
for f in existing_files[:5]:
    size_mb = f.stat().st_size / (1024*1024)
    print(f"  - {f.name}: {size_mb:.1f} MB")

print("\nSTEP 2: Loading V15 Datasets")
print("-" * 80)

v15_examples = []
try:
    # Load V15 gold dataset
    if V15_GOLD.exists():
        with open(V15_GOLD, 'r') as f:
            for line in f:
                try:
                    v15_examples.append(json.loads(line))
                except:
                    pass
        print(f"✓ Loaded {len(v15_examples)} examples from v15_gold.jsonl")

    # Load V15 enhanced dataset
    if V15_ENHANCED.exists():
        with open(V15_ENHANCED, 'r') as f:
            for line in f:
                try:
                    v15_examples.append(json.loads(line))
                except:
                    pass
        print(f"✓ Loaded additional examples from v15_enhanced.jsonl")
        print(f"✓ Total V15 examples: {len(v15_examples):,}")
except Exception as e:
    print(f"⚠ Error loading datasets: {e}")

print("\nSTEP 3: Dataset Composition Plan")
print("-" * 80)

composition = {
    "qa_pairs": {
        "percentage": 40,
        "description": "Code understanding + explanation",
        "target_count": 4000
    },
    "code_generation": {
        "percentage": 30,
        "description": "Generate code from requirements",
        "target_count": 3000
    },
    "code_refactoring": {
        "percentage": 20,
        "description": "Improve code quality",
        "target_count": 2000
    },
    "bug_fixing": {
        "percentage": 10,
        "description": "Fix bugs and issues",
        "target_count": 1000
    }
}

total_target = sum(c["target_count"] for c in composition.values())
print(f"Target training examples: {total_target:,}")
print("\nComposition breakdown:")
for category, details in composition.items():
    print(f"  {category}: {details['target_count']:,} ({details['percentage']}%)")

print("\nSTEP 4: Transforming V15 to V17 Format")
print("-" * 80)

v17_examples = []
categorized = {"qa_pairs": [], "code_generation": [], "code_refactoring": [], "bug_fixing": []}

# Transform V15 examples to V17 format
for example in v15_examples:
    try:
        # Categorize based on content
        if "question" in example or "Q:" in str(example.get("text", "")):
            categorized["qa_pairs"].append(example)
        elif "generate" in str(example.get("text", "")).lower():
            categorized["code_generation"].append(example)
        elif "refactor" in str(example.get("text", "")).lower():
            categorized["code_refactoring"].append(example)
        elif "fix" in str(example.get("text", "")).lower() or "bug" in str(example.get("text", "")).lower():
            categorized["bug_fixing"].append(example)
        else:
            categorized["qa_pairs"].append(example)  # Default to Q&A
    except:
        pass

print(f"Categorized examples:")
for category, examples in categorized.items():
    print(f"  {category}: {len(examples):,}")

print("\nSTEP 5: Creating V17 Dataset")
print("-" * 80)

# Sample from each category to meet targets
for category, target_count in [("qa_pairs", 4000), ("code_generation", 3000),
                                ("code_refactoring", 2000), ("bug_fixing", 1000)]:
    available = categorized[category]
    sample_size = min(target_count, len(available))
    sampled = random.sample(available, sample_size) if available else []
    v17_examples.extend(sampled)
    print(f"  {category}: {sample_size:,}/{target_count:,} examples")

print(f"\nTotal V17 examples: {len(v17_examples):,}")

# Shuffle
random.shuffle(v17_examples)

# Save V17 dataset
print("\nSTEP 6: Saving V17 Dataset")
print("-" * 80)

try:
    with open(V17_DATASET_FILE, 'w') as f:
        for example in v17_examples:
            f.write(json.dumps(example) + '\n')

    size_mb = V17_DATASET_FILE.stat().st_size / (1024*1024)
    print(f"✓ Saved {len(v17_examples):,} examples to v17_training_data.jsonl")
    print(f"✓ File size: {size_mb:.1f} MB")
except Exception as e:
    print(f"✗ Error saving dataset: {e}")

print("\n" + "="*80)
print("PHASE 2 STATUS: V17 DATASET CREATED")
print("="*80)
print(f"✓ Total examples: {len(v17_examples):,}")
print(f"✓ File: {V17_DATASET_FILE}")
print("="*80)

