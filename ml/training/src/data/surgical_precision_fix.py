#!/usr/bin/env python3
"""
SURGICAL PRECISION FIX - 100% Category Consistency
Fix all Motadata category inconsistencies
"""

import json
from pathlib import Path
from datetime import datetime

print("="*80)
print("V16.1 DATASET - SURGICAL PRECISION FIX")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

INPUT_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_final.jsonl")
OUTPUT_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_surgical.jsonl")

# Strict Q&A patterns
QA_PATTERNS = [
    "how does", "how do", "what does", "what do", "what is", "what are",
    "explain", "describe", "what's the purpose", "what's the difference",
    "why does", "why do", "when should", "when does", "where is", "where does",
    "which", "can you explain", "tell me about", "what happens"
]

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

print("\nSTEP 2: Identifying Motadata Inconsistencies")
print("-" * 80)

inconsistent_examples = []
motadata_examples = [ex for ex in examples if "type" in ex]

for idx, example in enumerate(motadata_examples):
    question = example.get("question", "").lower().strip()
    current_type = example.get("type", "")
    
    # Check if labeled as code_generation
    if current_type == "code_generation":
        # Verify it's actually code generation
        # If question starts with Q&A patterns, it's mislabeled
        is_qa = any(question.startswith(pattern) for pattern in QA_PATTERNS)
        
        if is_qa:
            inconsistent_examples.append({
                "index": idx,
                "question": question[:100],
                "current_type": current_type,
                "correct_type": "qa_pair"
            })

print(f"Found {len(inconsistent_examples)} inconsistent Motadata examples")

print("\nSTEP 3: Fixing Inconsistencies")
print("-" * 80)

fixed_count = 0
for example in examples:
    if "type" not in example:
        continue
    
    question = example.get("question", "").lower().strip()
    current_type = example.get("type", "")
    
    if current_type == "code_generation":
        # Check if it's actually Q&A
        is_qa = any(question.startswith(pattern) for pattern in QA_PATTERNS)
        
        if is_qa:
            example["type"] = "qa_pair"
            fixed_count += 1

print(f"✓ Fixed {fixed_count} examples")

print("\nSTEP 4: Final Category Distribution")
print("-" * 80)

motadata_qa = sum(1 for ex in examples if "type" in ex and ex["type"] == "qa_pair")
motadata_code = sum(1 for ex in examples if "type" in ex and ex["type"] == "code_generation")
v15_count = sum(1 for ex in examples if "messages" in ex)

print(f"V15 examples: {v15_count:,}")
print(f"Motadata Q&A: {motadata_qa:,} ({motadata_qa/(motadata_qa+motadata_code)*100:.1f}%)")
print(f"Motadata Code Gen: {motadata_code:,} ({motadata_code/(motadata_qa+motadata_code)*100:.1f}%)")
print(f"Total: {len(examples):,}")

print("\nSTEP 5: Verification - Check Remaining Code Gen Examples")
print("-" * 80)

remaining_code_gen = [ex for ex in examples if ex.get("type") == "code_generation"]
print(f"Remaining code_generation examples: {len(remaining_code_gen)}")

# Sample a few to verify
print("\nSample code_generation questions:")
for i, ex in enumerate(remaining_code_gen[:5]):
    print(f"  {i+1}. {ex.get('question', '')[:80]}...")

print("\nSTEP 6: Saving Surgically Precise Dataset")
print("-" * 80)

with open(OUTPUT_FILE, 'w') as f:
    for example in examples:
        f.write(json.dumps(example) + '\n')

file_size_mb = OUTPUT_FILE.stat().st_size / (1024*1024)
print(f"✓ Saved {len(examples):,} examples to v16_1_surgical.jsonl")
print(f"✓ File size: {file_size_mb:.1f} MB")

print("\n" + "="*80)
print("SURGICAL PRECISION FIX COMPLETE")
print("="*80)
print(f"Total Examples: {len(examples):,}")
print(f"Fixed: {fixed_count}")
print(f"Motadata Q&A: {motadata_qa:,}")
print(f"Motadata Code Gen: {motadata_code:,}")
print(f"Output: {OUTPUT_FILE}")
print("="*80)

