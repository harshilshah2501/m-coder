#!/usr/bin/env python3
"""
Create stratified train/val/test splits from dataset

Splits: 80% train, 10% val, 10% test
Ensures category distribution is maintained in each split
"""

import json
from pathlib import Path
from collections import Counter
from sklearn.model_selection import train_test_split


def load_dataset(file_path: Path):
    """Load dataset from JSONL file."""
    examples = []
    with open(file_path, 'r') as f:
        for line in f:
            examples.append(json.loads(line))
    return examples


def get_categories(examples):
    """Extract categories from examples."""
    return [ex.get('metadata', {}).get('category', 'unknown') for ex in examples]


def create_splits(examples, test_size=0.2, val_size=0.5, random_state=42):
    """
    Create stratified train/val/test splits.
    
    Args:
        examples: List of examples
        test_size: Fraction for test+val (0.2 = 20%)
        val_size: Fraction of test+val to use for val (0.5 = 50% of 20% = 10%)
        random_state: Random seed for reproducibility
    
    Returns:
        train, val, test splits
    """
    categories = get_categories(examples)
    
    # First split: train vs (val+test)
    train, temp = train_test_split(
        examples,
        test_size=test_size,
        stratify=categories,
        random_state=random_state
    )
    
    # Second split: val vs test
    temp_categories = get_categories(temp)
    val, test = train_test_split(
        temp,
        test_size=val_size,
        stratify=temp_categories,
        random_state=random_state
    )
    
    return train, val, test


def save_split(examples, output_path: Path):
    """Save split to JSONL file."""
    with open(output_path, 'w') as f:
        for example in examples:
            f.write(json.dumps(example) + '\n')


def print_split_stats(train, val, test):
    """Print statistics about splits."""
    print("\n" + "="*80)
    print("SPLIT STATISTICS")
    print("="*80)
    
    total = len(train) + len(val) + len(test)
    
    print(f"\nTotal examples: {total}")
    print(f"  Training:   {len(train):4d} ({len(train)/total*100:5.1f}%)")
    print(f"  Validation: {len(val):4d} ({len(val)/total*100:5.1f}%)")
    print(f"  Test:       {len(test):4d} ({len(test)/total*100:5.1f}%)")
    
    # Category distribution per split
    print("\n" + "-"*80)
    print("Category Distribution per Split:")
    print("-"*80)
    
    for split_name, split_data in [('Training', train), ('Validation', val), ('Test', test)]:
        categories = get_categories(split_data)
        counter = Counter(categories)
        
        print(f"\n{split_name}:")
        for cat, count in sorted(counter.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(split_data) * 100
            print(f"  {cat:20s}: {count:4d} ({pct:5.1f}%)")


def main():
    workspace_root = Path('/home/harshil/Harshil-PoCs')
    input_file = workspace_root / 'datasets' / 'v15_final.jsonl'
    output_dir = workspace_root / 'datasets' / 'splits'
    
    output_dir.mkdir(exist_ok=True)
    
    print("="*80)
    print("Creating Stratified Train/Val/Test Splits")
    print("="*80)
    print(f"\nInput: {input_file}")
    print(f"Output directory: {output_dir}")
    
    # Load dataset
    print("\nLoading dataset...")
    examples = load_dataset(input_file)
    print(f"✓ Loaded {len(examples)} examples")
    
    # Create splits
    print("\nCreating stratified splits (80/10/10)...")
    train, val, test = create_splits(examples)
    
    # Save splits
    print("\nSaving splits...")
    save_split(train, output_dir / 'train.jsonl')
    print(f"✓ Saved training set: {len(train)} examples")
    
    save_split(val, output_dir / 'val.jsonl')
    print(f"✓ Saved validation set: {len(val)} examples")
    
    save_split(test, output_dir / 'test.jsonl')
    print(f"✓ Saved test set: {len(test)} examples")
    
    # Print statistics
    print_split_stats(train, val, test)
    
    print("\n" + "="*80)
    print("✅ Splits Created Successfully!")
    print("="*80)
    print(f"\nOutput files:")
    print(f"  {output_dir / 'train.jsonl'}")
    print(f"  {output_dir / 'val.jsonl'}")
    print(f"  {output_dir / 'test.jsonl'}")
    print()


if __name__ == '__main__':
    main()

