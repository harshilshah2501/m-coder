#!/usr/bin/env python3
"""
Validate V15 balanced dataset.

Checks:
1. All capabilities present
2. Proper balance (no mode collapse)
3. Quality filters (valid diffs, proper format)
4. Tool use examples end with code generation
5. No tool obsession patterns

Usage:
    python3 validate_v15_dataset.py
"""

import json
from pathlib import Path
from typing import Dict, List
import re

import sys

# Support both original and converted datasets
if len(sys.argv) > 1:
    V15_FILE = Path(sys.argv[1])
else:
    # Try converted version first, fall back to original
    converted = Path("evaluation/finetuning/v15_balanced_search_replace.jsonl")
    original = Path("evaluation/finetuning/v15_balanced.jsonl")

    if converted.exists():
        V15_FILE = converted
    else:
        V15_FILE = original

# Expected ranges
EXPECTED_RANGES = {
    'tool_use': (10, 20),  # 10-20%
    'direct_generation': (25, 35),  # 25-35%
    'single_file': (20, 30),  # 20-30%
    'multi_file': (10, 15),  # 10-15%
    'code_review': (10, 15),  # 10-15%
    'file_creation': (4, 8),  # 4-8%
    'refactoring': (1, 4),  # 1-4%
}


def classify_example(example: dict) -> str:
    """Classify an example (same logic as create script)."""
    messages = example.get('messages', [])
    metadata = example.get('metadata', {})

    # First check if metadata has explicit category
    if 'category' in metadata:
        return metadata['category']

    has_tool_role = any(m.get('role') == 'tool' for m in messages)
    has_tool_calls = any('tool_calls' in str(m.get('content', '')) for m in messages)

    if has_tool_role or has_tool_calls:
        return 'tool_use'

    task = metadata.get('task', '').lower()
    
    if 'refactor' in task or 'cleanup' in task or 'optimize' in task:
        return 'refactoring'
    
    if 'review' in task or 'analyze' in task:
        return 'code_review'
    
    if metadata.get('files_count', 0) >= 3:
        return 'multi_file'
    
    assistant_msg = next((m.get('content', '') for m in messages if m.get('role') == 'assistant'), '')
    if '/dev/null' in assistant_msg or '--- /dev/null' in assistant_msg:
        return 'file_creation'
    
    file_count = assistant_msg.count('File:')
    if file_count == 1:
        return 'single_file'
    elif file_count > 1:
        return 'multi_file'
    
    return 'direct_generation'


def validate_tool_example(example: dict) -> List[str]:
    """Validate tool use example."""
    issues = []
    messages = example.get('messages', [])
    
    # Count tool calls
    tool_count = sum(1 for m in messages if m.get('role') == 'tool')
    if tool_count == 0:
        issues.append("No tool calls found")
    elif tool_count > 3:
        issues.append(f"Too many tool calls ({tool_count} > 3)")
    
    # Check last assistant message
    last_assistant = None
    for m in reversed(messages):
        if m.get('role') == 'assistant':
            last_assistant = m.get('content', '')
            break
    
    if not last_assistant:
        issues.append("No assistant response")
    elif '```diff' not in last_assistant and '<code>' not in last_assistant:
        issues.append("Tool example doesn't end with code generation")
    
    return issues


def validate_code_example(example: dict, category: str) -> List[str]:
    """Validate code generation example."""
    issues = []
    messages = example.get('messages', [])
    
    assistant_msg = next((m.get('content', '') for m in messages if m.get('role') == 'assistant'), '')
    
    if not assistant_msg:
        issues.append("No assistant message")
        return issues
    
    # Check for diff format
    if '```diff' not in assistant_msg and 'diff --git' not in assistant_msg:
        issues.append("No diff block found")
    
    # Check for hunks
    if '@@' not in assistant_msg:
        issues.append("No diff hunks found")
    
    # Check for thinking block (optional but recommended)
    if '<thinking>' not in assistant_msg and '<thought>' not in assistant_msg:
        issues.append("No thinking block (warning)")
    
    return issues


def main():
    """Main validation."""
    print("=" * 60)
    print("V15 Dataset Validation")
    print("=" * 60)
    
    if not V15_FILE.exists():
        print(f"❌ Error: {V15_FILE} not found")
        return 1
    
    # Load and classify
    examples = []
    categorized = {cat: [] for cat in EXPECTED_RANGES.keys()}
    
    print(f"\n📂 Loading {V15_FILE}...")
    
    with open(V15_FILE) as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                example = json.loads(line)
                examples.append(example)
                category = classify_example(example)
                categorized[category].append(example)
            except Exception as e:
                print(f"❌ Line {i}: Parse error: {e}")
    
    total = len(examples)
    print(f"✅ Loaded {total} examples")
    
    # Check composition
    print("\n" + "=" * 60)
    print("Composition Check")
    print("=" * 60)
    print(f"{'Category':<20s} {'Count':>6s} {'%':>6s} {'Expected':>12s} {'Status':>8s}")
    print("-" * 60)
    
    composition_ok = True
    for cat, (min_pct, max_pct) in EXPECTED_RANGES.items():
        count = len(categorized[cat])
        pct = (count / total * 100) if total > 0 else 0
        
        if min_pct <= pct <= max_pct:
            status = "✅"
        else:
            status = "❌"
            composition_ok = False
        
        print(f"{cat:<20s} {count:6d} {pct:5.1f}% {min_pct:2.0f}-{max_pct:2.0f}% {status:>8s}")
    
    print("-" * 60)
    print(f"{'TOTAL':<20s} {total:6d} {100.0:5.1f}%")
    
    if composition_ok:
        print("\n✅ Composition balanced")
    else:
        print("\n⚠️  Composition out of balance")

    # Quality checks
    print("\n" + "=" * 60)
    print("Quality Checks")
    print("=" * 60)

    total_issues = 0
    category_issues = {cat: [] for cat in EXPECTED_RANGES.keys()}

    for cat, examples_list in categorized.items():
        print(f"\n{cat} ({len(examples_list)} examples):")

        for i, example in enumerate(examples_list[:10]):  # Check first 10 of each
            if cat == 'tool_use':
                issues = validate_tool_example(example)
            else:
                issues = validate_code_example(example, cat)

            if issues:
                total_issues += len(issues)
                category_issues[cat].extend(issues)
                print(f"  Example {i+1}: {', '.join(issues)}")

    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    print(f"\nTotal examples: {total}")
    print(f"Composition: {'✅ Balanced' if composition_ok else '⚠️  Out of balance'}")
    print(f"Quality issues: {total_issues}")

    # Critical checks
    print("\n" + "=" * 60)
    print("Critical Checks")
    print("=" * 60)

    tool_count = len(categorized['tool_use'])
    tool_pct = (tool_count / total * 100) if total > 0 else 0

    multifile_count = len(categorized['multi_file'])
    multifile_pct = (multifile_count / total * 100) if total > 0 else 0

    direct_count = len(categorized['direct_generation'])
    direct_pct = (direct_count / total * 100) if total > 0 else 0

    checks_passed = 0
    checks_total = 5

    # Check 1: Tool use present but not dominant
    if 10 <= tool_pct <= 20:
        print("✅ Tool use balanced (10-20%)")
        checks_passed += 1
    else:
        print(f"❌ Tool use out of range: {tool_pct:.1f}%")

    # Check 2: Multi-file present
    if multifile_count >= 100:
        print(f"✅ Multi-file examples sufficient ({multifile_count})")
        checks_passed += 1
    else:
        print(f"⚠️  Multi-file examples low ({multifile_count})")

    # Check 3: Direct generation dominant
    if 25 <= direct_pct <= 35:
        print("✅ Direct generation balanced (25-35%)")
        checks_passed += 1
    else:
        print(f"⚠️  Direct generation: {direct_pct:.1f}%")

    # Check 4: Total count reasonable
    if total >= 2000:
        print(f"✅ Total examples sufficient ({total})")
        checks_passed += 1
    else:
        print(f"⚠️  Total examples low ({total})")

    # Check 5: All capabilities present
    missing = [cat for cat, examples_list in categorized.items() if len(examples_list) == 0]
    if not missing:
        print("✅ All capabilities present")
        checks_passed += 1
    else:
        print(f"❌ Missing capabilities: {', '.join(missing)}")

    # Final verdict
    print("\n" + "=" * 60)
    print("Final Verdict")
    print("=" * 60)

    print(f"\nPassed {checks_passed}/{checks_total} critical checks")

    if checks_passed == checks_total and composition_ok:
        print("\n✅ V15 dataset is VALID and ready for training!")
        return 0
    elif checks_passed >= 3:
        print("\n⚠️  V15 dataset has warnings but may be usable")
        return 0
    else:
        print("\n❌ V15 dataset has critical issues - needs fixes")
        return 1


if __name__ == '__main__':
    exit(main())

