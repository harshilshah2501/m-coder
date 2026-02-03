#!/usr/bin/env python3
"""
Remove duplicates from V15 dataset and backfill from available pool.

Strategy:
1. Load V15 dataset
2. Identify and remove duplicates
3. Backfill from the available pool to maintain target counts
4. Write deduplicated dataset

Usage:
    python3 remove_v15_duplicates.py
"""

import json
import random
from pathlib import Path
from collections import defaultdict

random.seed(42)

# Files
V15_FILE = Path("evaluation/finetuning/v15_balanced.jsonl")
V15_DEDUP_FILE = Path("evaluation/finetuning/v15_balanced_dedup.jsonl")

# Source files for backfilling
V12_FILE = Path("evaluation/finetuning/v12_combined.jsonl")
V13_FILE = Path("evaluation/finetuning/v13_combined.jsonl")
V14_FILE = Path("evaluation/finetuning/v14_multifile_final.jsonl")
V15_ADDITIONAL_FILE = Path("evaluation/finetuning/v15_additional.jsonl")
V15_MISSING_FILE = Path("evaluation/finetuning/v15_missing_capabilities.jsonl")

# Target counts
TARGET_COUNTS = {
    'direct_generation': 800,
    'tool_use': 400,
    'single_file': 600,
    'multi_file': 300,
    'code_review': 300,
    'file_creation': 150,
    'refactoring': 50,
}


def load_examples(file_path: Path) -> list:
    """Load examples from JSONL file."""
    examples = []
    if not file_path.exists():
        return examples
    
    with open(file_path) as f:
        for line in f:
            if line.strip():
                try:
                    examples.append(json.loads(line))
                except:
                    pass
    return examples


def remove_duplicates(examples: list) -> tuple:
    """Remove duplicates and return (unique_examples, duplicate_indices, category_counts)."""
    seen = {}
    unique = []
    duplicate_indices = []
    category_counts = defaultdict(int)
    
    for i, ex in enumerate(examples):
        # Create key from messages
        msgs = ex.get('messages', [])
        key = json.dumps(msgs, sort_keys=True)
        
        if key in seen:
            duplicate_indices.append(i)
            cat = ex.get('metadata', {}).get('category', 'unknown')
            category_counts[cat] += 1
        else:
            seen[key] = i
            unique.append(ex)
    
    return unique, duplicate_indices, category_counts


def main():
    """Main entry point."""
    print("=" * 60)
    print("V15 Duplicate Removal & Backfill")
    print("=" * 60)
    
    # Load V15 dataset
    print("\n📂 Loading V15 dataset...")
    v15_examples = load_examples(V15_FILE)
    print(f"✅ Loaded {len(v15_examples)} examples")
    
    # Remove duplicates
    print("\n🔍 Removing duplicates...")
    unique_examples, dup_indices, dup_by_cat = remove_duplicates(v15_examples)
    
    print(f"✅ Removed {len(dup_indices)} duplicates")
    print(f"✅ Remaining: {len(unique_examples)} unique examples")
    
    print(f"\nDuplicates by category:")
    for cat, count in sorted(dup_by_cat.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    # Count by category
    current_counts = defaultdict(int)
    for ex in unique_examples:
        cat = ex.get('metadata', {}).get('category', 'unknown')
        current_counts[cat] += 1
    
    print(f"\nCurrent counts after deduplication:")
    for cat in TARGET_COUNTS.keys():
        current = current_counts[cat]
        target = TARGET_COUNTS[cat]
        deficit = target - current
        status = "✅" if deficit <= 0 else f"⚠️  Need {deficit} more"
        print(f"  {cat:20s}: {current:4d} / {target:4d} {status}")
    
    # Calculate deficits
    deficits = {}
    for cat, target in TARGET_COUNTS.items():
        current = current_counts[cat]
        if current < target:
            deficits[cat] = target - current
    
    if deficits:
        print(f"\n📊 Need to backfill {sum(deficits.values())} examples")
        
        # Load source files for backfilling
        print("\n📂 Loading source files for backfilling...")
        # Import the classifier from create script
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from create_v15_balanced_dataset import classify_example, is_valid_example
        
        all_sources = []
        for source_file in [V12_FILE, V13_FILE, V14_FILE, V15_ADDITIONAL_FILE, V15_MISSING_FILE]:
            if source_file.exists():
                all_sources.extend(load_examples(source_file))
        
        print(f"✅ Loaded {len(all_sources)} source examples")
        
        # Categorize sources
        print("\n🔍 Categorizing source examples...")
        categorized_sources = defaultdict(list)
        for ex in all_sources:
            cat = classify_example(ex)
            if is_valid_example(ex, cat):
                categorized_sources[cat].append(ex)
        
        # Remove examples already in unique set
        print("\n🔍 Filtering out existing examples...")
        existing_keys = set()
        for ex in unique_examples:
            msgs = ex.get('messages', [])
            key = json.dumps(msgs, sort_keys=True)
            existing_keys.add(key)
        
        filtered_sources = defaultdict(list)
        for cat, examples in categorized_sources.items():
            for ex in examples:
                msgs = ex.get('messages', [])
                key = json.dumps(msgs, sort_keys=True)
                if key not in existing_keys:
                    filtered_sources[cat].append(ex)
        
        print(f"✅ Available for backfill:")
        for cat in TARGET_COUNTS.keys():
            print(f"  {cat:20s}: {len(filtered_sources[cat])} available")
        
        # Backfill
        print("\n📝 Backfilling...")
        for cat, deficit in deficits.items():
            available = filtered_sources[cat]
            if len(available) >= deficit:
                backfill = random.sample(available, deficit)
                for ex in backfill:
                    if 'metadata' not in ex:
                        ex['metadata'] = {}
                    ex['metadata']['category'] = cat
                unique_examples.extend(backfill)
                print(f"  ✅ {cat:20s}: Added {deficit} examples")
            else:
                for ex in available:
                    if 'metadata' not in ex:
                        ex['metadata'] = {}
                    ex['metadata']['category'] = cat
                unique_examples.extend(available)
                print(f"  ⚠️  {cat:20s}: Added {len(available)} (wanted {deficit})")
    
    # Shuffle final dataset
    random.shuffle(unique_examples)
    
    # Write output
    print(f"\n📝 Writing deduplicated dataset...")
    with open(V15_DEDUP_FILE, 'w') as f:
        for ex in unique_examples:
            f.write(json.dumps(ex) + '\n')
    
    print(f"✅ Wrote {len(unique_examples)} examples to {V15_DEDUP_FILE}")
    
    # Final stats
    final_counts = defaultdict(int)
    for ex in unique_examples:
        cat = ex.get('metadata', {}).get('category', 'unknown')
        final_counts[cat] += 1
    
    print("\n" + "=" * 60)
    print("Final Dataset Composition")
    print("=" * 60)
    print(f"{'Category':<20s} {'Count':>6s} {'%':>6s} {'Target':>6s}")
    print("-" * 60)
    
    total = len(unique_examples)
    for cat in TARGET_COUNTS.keys():
        count = final_counts[cat]
        pct = (count / total * 100) if total > 0 else 0
        target = TARGET_COUNTS[cat]
        print(f"{cat:<20s} {count:6d} {pct:5.1f}% {target:6d}")
    
    print("-" * 60)
    print(f"{'TOTAL':<20s} {total:6d} {100.0:5.1f}% {sum(TARGET_COUNTS.values()):6d}")
    
    print("\n" + "=" * 60)
    print("✅ Deduplication Complete!")
    print("=" * 60)
    print(f"\nNext step: Rename {V15_DEDUP_FILE} to {V15_FILE}")
    
    return 0


if __name__ == '__main__':
    exit(main())

