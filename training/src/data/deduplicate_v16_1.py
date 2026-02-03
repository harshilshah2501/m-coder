#!/usr/bin/env python3
"""
Remove duplicates from V16.1 dataset
Keep first occurrence, remove subsequent duplicates
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime

print("="*80)
print("V16.1 DATASET - DEDUPLICATION")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

INPUT_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_upgraded.jsonl")
OUTPUT_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_upgraded_dedup.jsonl")

print("STEP 1: Loading Dataset")
print("-" * 80)

examples = []
with open(INPUT_FILE, 'r') as f:
    for line in f:
        try:
            examples.append(json.loads(line))
        except:
            pass

print(f"✓ Loaded {len(examples):,} examples")

print("\nSTEP 2: Detecting Duplicates")
print("-" * 80)

seen_hashes = set()
unique_examples = []
duplicates_removed = 0

for example in examples:
    # Create hash from content
    if "messages" in example:
        content = json.dumps(example["messages"], sort_keys=True)
    else:
        content = f"{example.get('question', '')}{example.get('code', '')}"
    
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    if content_hash not in seen_hashes:
        seen_hashes.add(content_hash)
        unique_examples.append(example)
    else:
        duplicates_removed += 1

print(f"✓ Unique examples: {len(unique_examples):,}")
print(f"✓ Duplicates removed: {duplicates_removed}")

print("\nSTEP 3: Saving Deduplicated Dataset")
print("-" * 80)

with open(OUTPUT_FILE, 'w') as f:
    for example in unique_examples:
        f.write(json.dumps(example) + '\n')

file_size_mb = OUTPUT_FILE.stat().st_size / (1024*1024)
print(f"✓ Saved {len(unique_examples):,} examples to v16_1_upgraded_dedup.jsonl")
print(f"✓ File size: {file_size_mb:.1f} MB")

print("\n" + "="*80)
print("DEDUPLICATION COMPLETE")
print("="*80)
print(f"Original: {len(examples):,} examples")
print(f"Deduplicated: {len(unique_examples):,} examples")
print(f"Removed: {duplicates_removed} duplicates")
print(f"Output: {OUTPUT_FILE}")
print("="*80)

