#!/usr/bin/env python3
"""
Extract REAL Motadata codebase examples for V17 training
Only uses actual code from the Motadata repository
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime

print("="*80)
print("EXTRACTING REAL MOTADATA EXAMPLES FOR V17")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

MOTADATA_ROOT = Path("/home/harshil/TestMotadataProject/Motadata/motadata")
OUTPUT_DIR = Path("/home/harshil/Harshil-PoCs/datasets")
OUTPUT_FILE = OUTPUT_DIR / "v17_motadata_examples.jsonl"

print("STEP 1: Scanning Motadata Codebase")
print("-" * 80)

# Find all Java files
java_files = list(MOTADATA_ROOT.rglob("*.java"))
print(f"Found {len(java_files)} Java files")

# Categorize files
test_files = [f for f in java_files if "/test/" in str(f)]
main_files = [f for f in java_files if "/main/" in str(f)]

print(f"  Main source files: {len(main_files)}")
print(f"  Test files: {len(test_files)}")

print("\nSTEP 2: Validation Requirements")
print("-" * 80)

validation_rules = {
    "has_class_definition": "Must have a class definition",
    "has_methods": "Must have at least one method",
    "has_javadoc": "Should have JavaDoc comments",
    "valid_syntax": "Must be valid Java syntax",
    "meaningful_code": "Must have meaningful implementation (>50 chars)"
}

for rule, description in validation_rules.items():
    print(f"  ✓ {rule}: {description}")

print("\nSTEP 3: Extraction Strategy")
print("-" * 80)

extraction_strategy = {
    "Q&A Pairs (40%)": [
        "Extract class definitions with JavaDoc",
        "Extract method signatures with documentation",
        "Create Q&A: 'What does this class/method do?'",
        "Answer: Extract from JavaDoc + code analysis"
    ],
    "Code Generation (30%)": [
        "Extract method implementations",
        "Create Q&A: 'How to implement [functionality]?'",
        "Answer: Show the actual implementation"
    ],
    "Code Patterns (20%)": [
        "Extract common patterns (caching, error handling)",
        "Create Q&A: 'Show pattern for [use case]'",
        "Answer: Real Motadata implementation"
    ],
    "Integration Examples (10%)": [
        "Extract integration code",
        "Create Q&A: 'How to integrate [component]?'",
        "Answer: Real integration code from Motadata"
    ]
}

for category, steps in extraction_strategy.items():
    print(f"\n  {category}:")
    for step in steps:
        print(f"    - {step}")

print("\nSTEP 4: Data Consistency Checks")
print("-" * 80)

consistency_checks = {
    "No synthetic data": "All examples must be from actual Motadata code",
    "Real class names": "Use actual Motadata class names (LogPatternCacheStore, etc)",
    "Real method names": "Use actual method names from codebase",
    "Real imports": "Use actual import statements from Motadata",
    "Consistent formatting": "All code examples properly formatted",
    "Valid JSON": "All entries are valid JSONL format",
    "Required fields": "Each entry has: code, question, answer, source_file, line_number"
}

for check, requirement in consistency_checks.items():
    print(f"  ✓ {check}: {requirement}")

print("\nSTEP 5: Example Entry Format")
print("-" * 80)

example_format = {
    "type": "qa_pair | code_generation | code_pattern | integration",
    "question": "Real question about the code",
    "answer": "Answer based on actual code",
    "code": "Actual code snippet from Motadata",
    "source_file": "Path to source file in Motadata",
    "line_number": "Starting line number in source",
    "class_name": "Actual class name",
    "method_name": "Actual method name (if applicable)",
    "package": "Java package name",
    "difficulty": "beginner | intermediate | advanced",
    "tags": ["tag1", "tag2"]
}

print("Required fields in each entry:")
for field, description in example_format.items():
    print(f"  - {field}: {description}")

print("\n" + "="*80)
print("STEP 6: Ready to Extract Real Examples")
print("="*80)
print(f"\nNext steps:")
print(f"  1. Parse {len(main_files)} main source files")
print(f"  2. Extract class/method definitions with JavaDoc")
print(f"  3. Generate Q&A pairs from actual code")
print(f"  4. Validate all entries for consistency")
print(f"  5. Save to: {OUTPUT_FILE}")
print(f"\nExpected output: 10,000+ real Motadata examples")
print("="*80)

