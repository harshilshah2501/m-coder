#!/usr/bin/env python3
"""
Surgical Precision Validation for V16.1 Dataset
100% consistency check before training
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

print("="*80)
print("V16.1 DATASET - SURGICAL PRECISION VALIDATION")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

DATASET_FILE = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_upgraded.jsonl")

# Validation results
validation_results = {
    "total_examples": 0,
    "valid_examples": 0,
    "invalid_examples": [],
    "duplicates": [],
    "field_issues": [],
    "content_issues": [],
    "format_issues": []
}

print("STEP 1: Loading and Parsing")
print("-" * 80)

examples = []
line_num = 0
parse_errors = 0

with open(DATASET_FILE, 'r') as f:
    for line in f:
        line_num += 1
        try:
            example = json.loads(line)
            examples.append((line_num, example))
        except json.JSONDecodeError as e:
            parse_errors += 1
            validation_results["format_issues"].append({
                "line": line_num,
                "error": f"JSON parse error: {str(e)}"
            })

validation_results["total_examples"] = len(examples)
print(f"✓ Loaded {len(examples):,} examples")
if parse_errors > 0:
    print(f"✗ Parse errors: {parse_errors}")
else:
    print(f"✓ No parse errors")

print("\nSTEP 2: Field Validation")
print("-" * 80)

# Required fields for V15 examples (messages format)
v15_required = ["messages"]
# Required fields for Motadata examples
motadata_required = ["type", "question", "answer", "code", "source_file", 
                     "class_name", "package", "difficulty", "tags"]

field_complete = 0
for line_num, example in examples:
    # Check if V15 format (messages) or Motadata format
    if "messages" in example:
        # V15 format
        missing = [f for f in v15_required if f not in example]
        if not missing:
            # Validate messages structure
            if isinstance(example["messages"], list) and len(example["messages"]) > 0:
                field_complete += 1
            else:
                validation_results["field_issues"].append({
                    "line": line_num,
                    "error": "Invalid messages structure"
                })
        else:
            validation_results["field_issues"].append({
                "line": line_num,
                "missing_fields": missing
            })
    else:
        # Motadata format
        missing = [f for f in motadata_required if f not in example]
        if not missing:
            field_complete += 1
        else:
            validation_results["field_issues"].append({
                "line": line_num,
                "missing_fields": missing
            })

print(f"✓ Field complete: {field_complete:,}/{len(examples):,} ({field_complete/len(examples)*100:.2f}%)")
if validation_results["field_issues"]:
    print(f"✗ Field issues: {len(validation_results['field_issues'])}")

print("\nSTEP 3: Content Quality Validation")
print("-" * 80)

content_valid = 0
for line_num, example in examples:
    issues = []
    
    if "messages" in example:
        # V15 format validation
        messages = example.get("messages", [])
        if not messages:
            issues.append("Empty messages")
        else:
            for msg in messages:
                if not isinstance(msg, dict):
                    issues.append("Invalid message format")
                elif "role" not in msg or "content" not in msg:
                    issues.append("Missing role or content in message")
                elif not msg.get("content", "").strip():
                    issues.append("Empty message content")
    else:
        # Motadata format validation
        if not example.get("question", "").strip():
            issues.append("Empty question")
        if not example.get("answer", "").strip():
            issues.append("Empty answer")
        if not example.get("code", "").strip():
            issues.append("Empty code")
        
        # Length checks
        if len(example.get("question", "")) < 10:
            issues.append("Question too short (<10 chars)")
        if len(example.get("answer", "")) < 20:
            issues.append("Answer too short (<20 chars)")
        if len(example.get("code", "")) < 10:
            issues.append("Code too short (<10 chars)")
    
    if issues:
        validation_results["content_issues"].append({
            "line": line_num,
            "issues": issues
        })
    else:
        content_valid += 1

print(f"✓ Content valid: {content_valid:,}/{len(examples):,} ({content_valid/len(examples)*100:.2f}%)")
if validation_results["content_issues"]:
    print(f"✗ Content issues: {len(validation_results['content_issues'])}")

print("\nSTEP 4: Duplicate Detection")
print("-" * 80)

# Hash-based duplicate detection
hashes = defaultdict(list)
for line_num, example in examples:
    # Create hash from content
    if "messages" in example:
        content = json.dumps(example["messages"], sort_keys=True)
    else:
        content = f"{example.get('question', '')}{example.get('code', '')}"
    
    content_hash = hashlib.md5(content.encode()).hexdigest()
    hashes[content_hash].append(line_num)

duplicates = {h: lines for h, lines in hashes.items() if len(lines) > 1}
if duplicates:
    validation_results["duplicates"] = [
        {"hash": h, "lines": lines} for h, lines in duplicates.items()
    ]
    print(f"✗ Duplicates found: {len(duplicates)} groups")
else:
    print(f"✓ No duplicates found")

print("\nSTEP 5: Final Validation")
print("-" * 80)

validation_results["valid_examples"] = (
    field_complete == len(examples) and
    content_valid == len(examples) and
    len(duplicates) == 0 and
    parse_errors == 0
)

if validation_results["valid_examples"]:
    print("✅ DATASET IS 100% VALID AND READY FOR TRAINING")
else:
    print("❌ DATASET HAS ISSUES - MUST FIX BEFORE TRAINING")

# Save validation report
report_file = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_validation_report.json")
with open(report_file, 'w') as f:
    json.dump(validation_results, f, indent=2)

print(f"\n✓ Validation report saved: {report_file}")

print("\n" + "="*80)
print("VALIDATION SUMMARY")
print("="*80)
print(f"Total Examples: {validation_results['total_examples']:,}")
print(f"Parse Errors: {len(validation_results['format_issues'])}")
print(f"Field Issues: {len(validation_results['field_issues'])}")
print(f"Content Issues: {len(validation_results['content_issues'])}")
print(f"Duplicates: {len(validation_results['duplicates'])}")
print("="*80)

