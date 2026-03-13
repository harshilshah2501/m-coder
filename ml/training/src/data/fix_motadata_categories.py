#!/usr/bin/env python3
"""
Fix Motadata category labels based on actual content
Reclassify based on question patterns
"""

import json
from pathlib import Path
from datetime import datetime

print("="*80)
print("V16.1 DATASET - FIX MOTADATA CATEGORIES")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

INPUT_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_upgraded_dedup.jsonl")
OUTPUT_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_final.jsonl")

# Q&A patterns (explanation/understanding questions)
QA_PATTERNS = [
    "how does", "what does", "what is", "explain", "describe",
    "what's the purpose", "what's the difference", "why does",
    "when should", "where is", "which", "can you explain"
]

# Code generation patterns (implementation requests)
CODE_GEN_PATTERNS = [
    "implement", "create", "write", "generate", "add",
    "complete", "fill in", "provide implementation"
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

print("\nSTEP 2: Analyzing and Fixing Motadata Categories")
print("-" * 80)

v15_count = 0
motadata_count = 0
reclassified = 0
qa_to_code = 0
code_to_qa = 0

for example in examples:
    if "messages" in example:
        # V15 example - keep as is
        v15_count += 1
    else:
        # Motadata example - check and fix category
        motadata_count += 1
        question = example.get("question", "").lower()
        current_type = example.get("type", "")
        
        # Determine correct type based on question
        is_qa_question = any(pattern in question for pattern in QA_PATTERNS)
        is_code_gen_question = any(pattern in question for pattern in CODE_GEN_PATTERNS)
        
        # Classify based on patterns
        if is_qa_question and not is_code_gen_question:
            # This is a Q&A question
            correct_type = "qa_pair"
        elif is_code_gen_question:
            # This is code generation
            correct_type = "code_generation"
        else:
            # Default: if it starts with "How does" or "What", it's Q&A
            # Otherwise, it's code generation
            if question.startswith(("how ", "what ", "why ", "when ", "where ", "which ")):
                correct_type = "qa_pair"
            else:
                correct_type = "code_generation"
        
        # Update if different
        if current_type != correct_type:
            reclassified += 1
            if current_type == "qa_pair" and correct_type == "code_generation":
                qa_to_code += 1
            elif current_type == "code_generation" and correct_type == "qa_pair":
                code_to_qa += 1
            example["type"] = correct_type

print(f"V15 examples: {v15_count:,}")
print(f"Motadata examples: {motadata_count:,}")
print(f"Reclassified: {reclassified:,}")
print(f"  QA → Code Gen: {qa_to_code}")
print(f"  Code Gen → QA: {code_to_qa}")

print("\nSTEP 3: Final Category Distribution")
print("-" * 80)

# Count final categories
motadata_qa = sum(1 for ex in examples if "type" in ex and ex["type"] == "qa_pair")
motadata_code = sum(1 for ex in examples if "type" in ex and ex["type"] == "code_generation")

print(f"Motadata Q&A: {motadata_qa:,} ({motadata_qa/motadata_count*100:.1f}%)")
print(f"Motadata Code Gen: {motadata_code:,} ({motadata_code/motadata_count*100:.1f}%)")

print("\nSTEP 4: Saving Fixed Dataset")
print("-" * 80)

with open(OUTPUT_FILE, 'w') as f:
    for example in examples:
        f.write(json.dumps(example) + '\n')

file_size_mb = OUTPUT_FILE.stat().st_size / (1024*1024)
print(f"✓ Saved {len(examples):,} examples to v16_1_final.jsonl")
print(f"✓ File size: {file_size_mb:.1f} MB")

print("\n" + "="*80)
print("CATEGORY FIX COMPLETE")
print("="*80)
print(f"Total Examples: {len(examples):,}")
print(f"Reclassified: {reclassified:,}")
print(f"Output: {OUTPUT_FILE}")
print("="*80)

