#!/usr/bin/env python3
"""
Create train/val/test splits for enhanced dataset
80/10/10 split with stratification by category
"""

import json
import random
from pathlib import Path
from collections import defaultdict

INPUT = "datasets/v15_enhanced.jsonl"
OUTPUT_DIR = "datasets/v15_enhanced_splits"

TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
TEST_RATIO = 0.10


def load_and_stratify(filepath):
    """Load examples and group by category"""
    by_category = defaultdict(list)
    
    with open(filepath, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                cat = data.get('metadata', {}).get('category', 'unknown')
                by_category[cat].append(data)
            except:
                pass
    
    return by_category


def create_stratified_splits(by_category):
    """Create stratified splits maintaining category distribution"""
    train = []
    val = []
    test = []
    
    for category, examples in by_category.items():
        # Shuffle within category
        random.shuffle(examples)
        
        n = len(examples)
        n_train = int(n * TRAIN_RATIO)
        n_val = int(n * VAL_RATIO)
        
        # Split
        cat_train = examples[:n_train]
        cat_val = examples[n_train:n_train + n_val]
        cat_test = examples[n_train + n_val:]
        
        train.extend(cat_train)
        val.extend(cat_val)
        test.extend(cat_test)
        
        print(f"  {category:<25} {len(cat_train):>4} / {len(cat_val):>4} / {len(cat_test):>4}")
    
    return train, val, test


def save_split(examples, filepath):
    """Save split to file"""
    with open(filepath, 'w') as f:
        for example in examples:
            f.write(json.dumps(example) + '\n')


def main():
    print("="*80)
    print("CREATE STRATIFIED SPLITS")
    print("="*80)
    print()
    
    # Create output directory
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    
    # Load and stratify
    print("📊 Loading dataset...")
    by_category = load_and_stratify(INPUT)
    total = sum(len(v) for v in by_category.values())
    print(f"✅ Loaded {total} examples across {len(by_category)} categories")
    print()
    
    # Create splits
    print("🔀 Creating stratified splits (80/10/10)...")
    print(f"{'Category':<25} {'Train':>6} / {'Val':>4} / {'Test':>4}")
    print("-"*80)
    
    train, val, test = create_stratified_splits(by_category)
    
    print("-"*80)
    print(f"{'TOTAL':<25} {len(train):>6} / {len(val):>4} / {len(test):>4}")
    print()
    
    # Shuffle final splits
    print("🔀 Shuffling splits...")
    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)
    print("✅ Shuffled")
    print()
    
    # Save splits
    print("💾 Saving splits...")
    save_split(train, output_dir / "train.jsonl")
    save_split(val, output_dir / "val.jsonl")
    save_split(test, output_dir / "test.jsonl")
    print(f"✅ Saved to {OUTPUT_DIR}/")
    print()
    
    # Verify
    print("="*80)
    print("SPLIT VERIFICATION")
    print("="*80)
    print(f"\nTrain: {len(train)} ({len(train)/total*100:.1f}%)")
    print(f"Val:   {len(val)} ({len(val)/total*100:.1f}%)")
    print(f"Test:  {len(test)} ({len(test)/total*100:.1f}%)")
    print(f"Total: {len(train) + len(val) + len(test)}")
    print()
    
    # Category distribution check
    print("Category distribution in splits:")
    print(f"{'Category':<25} {'Train %':>10} {'Val %':>10} {'Test %':>10}")
    print("-"*80)
    
    train_cats = defaultdict(int)
    val_cats = defaultdict(int)
    test_cats = defaultdict(int)
    
    for ex in train:
        train_cats[ex.get('metadata', {}).get('category', 'unknown')] += 1
    for ex in val:
        val_cats[ex.get('metadata', {}).get('category', 'unknown')] += 1
    for ex in test:
        test_cats[ex.get('metadata', {}).get('category', 'unknown')] += 1
    
    all_cats = set(train_cats.keys()) | set(val_cats.keys()) | set(test_cats.keys())
    
    for cat in sorted(all_cats):
        train_pct = (train_cats[cat] / len(train)) * 100 if train else 0
        val_pct = (val_cats[cat] / len(val)) * 100 if val else 0
        test_pct = (test_cats[cat] / len(test)) * 100 if test else 0
        print(f"{cat:<25} {train_pct:>9.1f}% {val_pct:>9.1f}% {test_pct:>9.1f}%")
    
    print()
    print("="*80)
    print("✅ SPLITS READY FOR TRAINING")
    print("="*80)


if __name__ == "__main__":
    random.seed(42)
    main()

