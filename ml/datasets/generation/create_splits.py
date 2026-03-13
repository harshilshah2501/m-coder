#!/usr/bin/env python3
"""
Create train/val/test splits for v17_dpo_pairs.jsonl

Stratified split by category to maintain distribution:
- Train: 80% (220 pairs)
- Val: 10% (28 pairs)
- Test: 10% (27 pairs)

Output:
- datasets/v17_dpo_pairs_train.jsonl
- datasets/v17_dpo_pairs_val.jsonl
- datasets/v17_dpo_pairs_test.jsonl
- datasets/v17_dpo_metadata.json
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
from sklearn.model_selection import train_test_split


BASE_DIR = Path("/home/harshil/Harshil-PoCs")
INPUT_FILE = BASE_DIR / "datasets/v17_dpo_pairs.jsonl"
METADATA_FILE = BASE_DIR / "datasets/v17_dpo_metadata.json"


def main():
    print("=" * 80)
    print("CREATING TRAIN/VAL/TEST SPLITS")
    print("=" * 80)
    
    # Load pairs
    print(f"\nLoading {INPUT_FILE.name}...")
    pairs = []
    with open(INPUT_FILE) as f:
        for line in f:
            pairs.append(json.loads(line))
    
    print(f"Loaded {len(pairs)} pairs")
    
    # Group by category for stratified split
    pairs_by_category = defaultdict(list)
    for pair in pairs:
        category = pair.get("category", "unknown")
        pairs_by_category[category].append(pair)
    
    print(f"\nCategory distribution:")
    for cat, items in sorted(pairs_by_category.items()):
        pct = (len(items) / len(pairs)) * 100
        print(f"  {cat:20s}: {len(items):3d} ({pct:5.1f}%)")
    
    # Stratified split per category
    train_pairs = []
    val_pairs = []
    test_pairs = []
    
    for category, items in pairs_by_category.items():
        # 80/10/10 split
        train, test = train_test_split(items, test_size=0.2, random_state=42)
        val, test = train_test_split(test, test_size=0.5, random_state=42)
        
        train_pairs.extend(train)
        val_pairs.extend(val)
        test_pairs.extend(test)
    
    print(f"\nSplit results:")
    print(f"  Train: {len(train_pairs)} ({(len(train_pairs)/len(pairs))*100:.1f}%)")
    print(f"  Val:   {len(val_pairs)} ({(len(val_pairs)/len(pairs))*100:.1f}%)")
    print(f"  Test:  {len(test_pairs)} ({(len(test_pairs)/len(pairs))*100:.1f}%)")
    
    # Save splits
    print(f"\nSaving splits...")
    
    train_file = BASE_DIR / "datasets/v17_dpo_pairs_train.jsonl"
    with open(train_file, 'w') as f:
        for pair in train_pairs:
            f.write(json.dumps(pair) + "\n")
    print(f"  ✓ {train_file.name}")
    
    val_file = BASE_DIR / "datasets/v17_dpo_pairs_val.jsonl"
    with open(val_file, 'w') as f:
        for pair in val_pairs:
            f.write(json.dumps(pair) + "\n")
    print(f"  ✓ {val_file.name}")
    
    test_file = BASE_DIR / "datasets/v17_dpo_pairs_test.jsonl"
    with open(test_file, 'w') as f:
        for pair in test_pairs:
            f.write(json.dumps(pair) + "\n")
    print(f"  ✓ {test_file.name}")
    
    # Compute metadata
    def compute_stats(data, name):
        sources = Counter(p.get("source") for p in data)
        difficulties = Counter(p.get("difficulty") for p in data)
        categories = Counter(p.get("category") for p in data)
        return {
            "count": len(data),
            "sources": dict(sources),
            "difficulties": dict(difficulties),
            "categories": dict(categories),
        }
    
    metadata = {
        "timestamp": str(Path.cwd()),
        "total_pairs": len(pairs),
        "splits": {
            "train": compute_stats(train_pairs, "train"),
            "val": compute_stats(val_pairs, "val"),
            "test": compute_stats(test_pairs, "test"),
        },
        "overall_distribution": {
            "by_category": dict(Counter(p.get("category") for p in pairs)),
            "by_source": dict(Counter(p.get("source") for p in pairs)),
            "by_difficulty": dict(Counter(p.get("difficulty") for p in pairs)),
        }
    }
    
    # Save metadata
    print(f"\nSaving metadata to {METADATA_FILE.name}...")
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(json.dumps(metadata, indent=2))
    print("\n" + "=" * 80)
    print("SPLITS CREATED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
