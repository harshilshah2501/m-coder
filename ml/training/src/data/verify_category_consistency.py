#!/usr/bin/env python3
"""
Verify category consistency in V16.1 dataset
Check that prompts and samples match their declared categories
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

print("="*80)
print("V16.1 DATASET - CATEGORY CONSISTENCY VERIFICATION")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

DATASET_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_upgraded_dedup.jsonl")

# Category patterns
CATEGORY_PATTERNS = {
    "code_generation": [
        "implement", "create", "write", "generate", "add method",
        "complete the implementation", "fill in the code"
    ],
    "refactoring": [
        "refactor", "improve", "optimize", "restructure", "clean up",
        "extract method", "rename", "simplify"
    ],
    "bug_fixing": [
        "fix", "debug", "resolve", "correct", "repair",
        "fix the bug", "solve the issue"
    ],
    "code_review": [
        "review", "analyze", "evaluate", "assess", "critique",
        "what does this code do", "explain this code"
    ],
    "testing": [
        "test", "unit test", "write test", "test case",
        "verify", "validate"
    ],
    "documentation": [
        "document", "javadoc", "comment", "describe",
        "add documentation", "explain"
    ],
    "qa_pairs": [
        "what is", "what does", "how does", "explain",
        "describe the purpose", "what's the difference"
    ]
}

print("STEP 1: Loading Dataset")
print("-" * 80)

examples = []
with open(DATASET_FILE, 'r') as f:
    for line in f:
        try:
            examples.append(json.loads(line))
        except:
            pass

print(f"✓ Loaded {len(examples):,} examples")

print("\nSTEP 2: Analyzing Categories")
print("-" * 80)

# Separate V15 and Motadata examples
v15_examples = [ex for ex in examples if "messages" in ex]
motadata_examples = [ex for ex in examples if "type" in ex]

print(f"V15 examples: {len(v15_examples):,}")
print(f"Motadata examples: {len(motadata_examples):,}")

print("\nSTEP 3: V15 Category Analysis")
print("-" * 80)

v15_categories = defaultdict(int)
v15_inconsistencies = []

for idx, example in enumerate(v15_examples):
    messages = example.get("messages", [])
    if not messages:
        continue
    
    # Get user message (task description)
    user_msg = None
    for msg in messages:
        if msg.get("role") == "user":
            user_msg = msg.get("content", "").lower()
            break
    
    if not user_msg:
        continue
    
    # Detect category from content
    detected_categories = []
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in user_msg:
                detected_categories.append(category)
                break
    
    # Get metadata category if exists
    metadata_category = example.get("metadata", {}).get("category", "unknown")
    
    if detected_categories:
        primary_category = detected_categories[0]
        v15_categories[primary_category] += 1
        
        # Check consistency
        if metadata_category != "unknown" and metadata_category not in detected_categories:
            v15_inconsistencies.append({
                "index": idx,
                "metadata_category": metadata_category,
                "detected_categories": detected_categories,
                "sample": user_msg[:200]
            })
    else:
        v15_categories["unclassified"] += 1

print("V15 Category Distribution:")
for category, count in sorted(v15_categories.items(), key=lambda x: x[1], reverse=True):
    print(f"  {category}: {count:,} ({count/len(v15_examples)*100:.1f}%)")

if v15_inconsistencies:
    print(f"\n⚠️  V15 Inconsistencies: {len(v15_inconsistencies)}")
    for inc in v15_inconsistencies[:5]:
        print(f"  - Metadata: {inc['metadata_category']}, Detected: {inc['detected_categories']}")
else:
    print(f"\n✓ No V15 inconsistencies detected")

print("\nSTEP 4: Motadata Category Analysis")
print("-" * 80)

motadata_categories = defaultdict(int)
motadata_inconsistencies = []

for idx, example in enumerate(motadata_examples):
    declared_type = example.get("type", "unknown")
    question = example.get("question", "").lower()
    answer = example.get("answer", "").lower()
    
    motadata_categories[declared_type] += 1
    
    # Verify consistency
    if declared_type == "qa_pair":
        # Should be question-answer format
        if not any(pattern in question for pattern in CATEGORY_PATTERNS["qa_pairs"]):
            motadata_inconsistencies.append({
                "index": idx,
                "type": declared_type,
                "issue": "QA pair doesn't have question pattern",
                "question": question[:150]
            })
    elif declared_type == "code_generation":
        # Should have implementation keywords
        if not any(pattern in question or pattern in answer for pattern in CATEGORY_PATTERNS["code_generation"]):
            motadata_inconsistencies.append({
                "index": idx,
                "type": declared_type,
                "issue": "Code generation doesn't have implementation keywords",
                "question": question[:150]
            })

print("Motadata Category Distribution:")
for category, count in sorted(motadata_categories.items(), key=lambda x: x[1], reverse=True):
    print(f"  {category}: {count:,} ({count/len(motadata_examples)*100:.1f}%)")

if motadata_inconsistencies:
    print(f"\n⚠️  Motadata Inconsistencies: {len(motadata_inconsistencies)}")
    for inc in motadata_inconsistencies[:5]:
        print(f"  - Type: {inc['type']}, Issue: {inc['issue']}")
else:
    print(f"\n✓ No Motadata inconsistencies detected")

print("\nSTEP 5: Overall Summary")
print("-" * 80)

total_inconsistencies = len(v15_inconsistencies) + len(motadata_inconsistencies)
consistency_rate = (len(examples) - total_inconsistencies) / len(examples) * 100

print(f"Total Examples: {len(examples):,}")
print(f"Inconsistencies: {total_inconsistencies}")
print(f"Consistency Rate: {consistency_rate:.2f}%")

if consistency_rate >= 99.0:
    print("\n✅ DATASET CATEGORIES ARE HIGHLY CONSISTENT")
elif consistency_rate >= 95.0:
    print("\n⚠️  DATASET HAS MINOR CATEGORY INCONSISTENCIES")
else:
    print("\n❌ DATASET HAS SIGNIFICANT CATEGORY INCONSISTENCIES")

# Save report
report = {
    "v15_categories": dict(v15_categories),
    "motadata_categories": dict(motadata_categories),
    "v15_inconsistencies": v15_inconsistencies[:20],
    "motadata_inconsistencies": motadata_inconsistencies[:20],
    "total_inconsistencies": total_inconsistencies,
    "consistency_rate": consistency_rate
}

report_file = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_category_consistency_report.json")
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n✓ Report saved: {report_file}")
print("="*80)

