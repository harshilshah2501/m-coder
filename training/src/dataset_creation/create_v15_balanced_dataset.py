#!/usr/bin/env python3
"""
Create V15 balanced dataset combining:
- V12 tool use examples (balanced)
- V13 direct generation examples
- V14 multi-file examples
- New capabilities (code review, file creation, refactoring)

Target composition:
- Direct Generation: 800 (30%)
- Tool Use (Balanced): 400 (15%)
- Single-File Edits: 600 (23%)
- Multi-File Commits: 300 (12%)
- Code Review: 300 (12%)
- File Creation: 150 (6%)
- Refactoring: 50 (2%)
Total: 2,600 examples

Usage:
    python3 create_v15_balanced_dataset.py
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional
import re

# Set random seed for reproducibility
random.seed(42)

# Input files
V12_FILE = Path("evaluation/finetuning/v12_combined.jsonl")
V13_FILE = Path("evaluation/finetuning/v13_combined.jsonl")
V14_FILE = Path("evaluation/finetuning/v14_multifile_final.jsonl")
V15_ADDITIONAL_FILE = Path("evaluation/finetuning/v15_additional.jsonl")
V15_MISSING_FILE = Path("evaluation/finetuning/v15_missing_capabilities.jsonl")

# Output file
V15_FILE = Path("evaluation/finetuning/v15_balanced.jsonl")

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

TOTAL_TARGET = sum(TARGET_COUNTS.values())


def classify_example(example: dict) -> str:
    """Classify an example into a capability category."""
    messages = example.get('messages', [])
    metadata = example.get('metadata', {})

    # First check if metadata has explicit category
    if 'category' in metadata:
        return metadata['category']

    # Check for tool use
    has_tool_role = any(m.get('role') == 'tool' for m in messages)
    has_tool_calls = any('tool_calls' in str(m.get('content', '')) for m in messages)

    if has_tool_role or has_tool_calls:
        return 'tool_use'

    # Check metadata for hints
    task = metadata.get('task', '').lower()
    
    # Check for refactoring
    if 'refactor' in task or 'cleanup' in task or 'optimize' in task:
        return 'refactoring'
    
    # Check for code review
    if 'review' in task or 'analyze' in task:
        return 'code_review'
    
    # Check for multi-file (from V14)
    if metadata.get('files_count', 0) >= 3:
        return 'multi_file'
    
    # Check for file creation (diff has /dev/null)
    assistant_msg = next((m.get('content', '') for m in messages if m.get('role') == 'assistant'), '')
    if '/dev/null' in assistant_msg or '--- /dev/null' in assistant_msg:
        return 'file_creation'
    
    # Check for single file vs multi-file
    file_count = assistant_msg.count('File:')
    if file_count == 1:
        return 'single_file'
    elif file_count > 1:
        return 'multi_file'
    
    # Default to direct generation
    return 'direct_generation'


def is_valid_tool_example(example: dict) -> bool:
    """
    Validate tool use example to prevent tool obsession.
    
    Requirements:
    1. Must have tool calls
    2. Must end with code generation (not just tools)
    3. Max 3 tool calls
    4. No circular tool use
    """
    messages = example.get('messages', [])
    
    # Count tool calls
    tool_count = sum(1 for m in messages if m.get('role') == 'tool')
    if tool_count == 0 or tool_count > 3:
        return False
    
    # Must end with assistant generating code
    last_assistant = None
    for m in reversed(messages):
        if m.get('role') == 'assistant':
            last_assistant = m.get('content', '')
            break
    
    if not last_assistant:
        return False
    
    # Must have code generation (diff or code block)
    has_code = '```diff' in last_assistant or '<code>' in last_assistant
    if not has_code:
        return False
    
    return True


def is_valid_example(example: dict, category: str) -> bool:
    """Validate example quality."""
    messages = example.get('messages', [])
    
    if not messages:
        return False
    
    # Get assistant message
    assistant_msg = next((m.get('content', '') for m in messages if m.get('role') == 'assistant'), '')
    
    if not assistant_msg:
        return False
    
    # Category-specific validation
    if category == 'tool_use':
        return is_valid_tool_example(example)
    
    # For code generation, must have diff format
    if category in ['direct_generation', 'single_file', 'multi_file', 'file_creation', 'refactoring']:
        has_diff = '```diff' in assistant_msg or 'diff --git' in assistant_msg
        has_hunks = '@@' in assistant_msg
        return has_diff and has_hunks
    
    return True


def load_and_classify(file_path: Path) -> Dict[str, List[dict]]:
    """Load examples and classify them by capability."""
    categorized = {cat: [] for cat in TARGET_COUNTS.keys()}
    
    print(f"\n📂 Loading {file_path.name}...")
    
    with open(file_path) as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                example = json.loads(line)
                category = classify_example(example)
                
                if is_valid_example(example, category):
                    categorized[category].append(example)
            except Exception as e:
                print(f"⚠️  Error parsing line: {e}")
                continue
    
    # Print stats
    for cat, examples in categorized.items():
        print(f"  {cat}: {len(examples)} examples")
    
    return categorized


def main():
    """Main entry point."""
    print("=" * 60)
    print("V15 Balanced Dataset Builder")
    print("=" * 60)

    # Load and classify all examples
    all_categorized = {cat: [] for cat in TARGET_COUNTS.keys()}

    # Load V12 (tool use + direct)
    v12_categorized = load_and_classify(V12_FILE)
    for cat, examples in v12_categorized.items():
        all_categorized[cat].extend(examples)

    # Load V13 (direct + single-file)
    v13_categorized = load_and_classify(V13_FILE)
    for cat, examples in v13_categorized.items():
        all_categorized[cat].extend(examples)

    # Load V14 (multi-file)
    v14_categorized = load_and_classify(V14_FILE)
    for cat, examples in v14_categorized.items():
        all_categorized[cat].extend(examples)

    # Load V15 additional (multi-file, refactoring, file creation)
    if V15_ADDITIONAL_FILE.exists():
        v15_additional_categorized = load_and_classify(V15_ADDITIONAL_FILE)
        for cat, examples in v15_additional_categorized.items():
            all_categorized[cat].extend(examples)

    # Load V15 missing capabilities (code review, file creation)
    if V15_MISSING_FILE.exists():
        v15_missing_categorized = load_and_classify(V15_MISSING_FILE)
        for cat, examples in v15_missing_categorized.items():
            all_categorized[cat].extend(examples)

    # Print total available
    print("\n" + "=" * 60)
    print("Total Available Examples by Category")
    print("=" * 60)
    total_available = 0
    for cat in TARGET_COUNTS.keys():
        count = len(all_categorized[cat])
        target = TARGET_COUNTS[cat]
        status = "✅" if count >= target else "⚠️"
        print(f"{status} {cat:20s}: {count:4d} available (target: {target})")
        total_available += count
    print(f"\nTotal available: {total_available}")
    print(f"Total target: {TOTAL_TARGET}")

    # Sample from each category
    print("\n" + "=" * 60)
    print("Sampling Examples")
    print("=" * 60)

    selected = []
    stats = {}

    for cat, target_count in TARGET_COUNTS.items():
        available = all_categorized[cat]

        if len(available) >= target_count:
            # Randomly sample target count
            sampled = random.sample(available, target_count)
            # Add category to metadata for each example
            for ex in sampled:
                if 'metadata' not in ex:
                    ex['metadata'] = {}
                ex['metadata']['category'] = cat
            selected.extend(sampled)
            stats[cat] = target_count
            print(f"✅ {cat:20s}: {target_count} selected")
        else:
            # Take all available
            # Add category to metadata for each example
            for ex in available:
                if 'metadata' not in ex:
                    ex['metadata'] = {}
                ex['metadata']['category'] = cat
            selected.extend(available)
            stats[cat] = len(available)
            print(f"⚠️  {cat:20s}: {len(available)} selected (wanted {target_count})")

    # Shuffle final dataset
    random.shuffle(selected)

    # Write output
    print("\n" + "=" * 60)
    print("Writing Output")
    print("=" * 60)

    with open(V15_FILE, 'w') as f:
        for example in selected:
            f.write(json.dumps(example) + '\n')

    print(f"✅ Wrote {len(selected)} examples to {V15_FILE}")

    # Print final stats
    print("\n" + "=" * 60)
    print("V15 Dataset Composition")
    print("=" * 60)
    print(f"{'Category':<20s} {'Count':>6s} {'%':>6s} {'Target':>6s}")
    print("-" * 60)

    total = len(selected)
    for cat in TARGET_COUNTS.keys():
        count = stats[cat]
        pct = (count / total * 100) if total > 0 else 0
        target = TARGET_COUNTS[cat]
        print(f"{cat:<20s} {count:6d} {pct:5.1f}% {target:6d}")

    print("-" * 60)
    print(f"{'TOTAL':<20s} {total:6d} {100.0:5.1f}% {TOTAL_TARGET:6d}")

    # Validation summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    # Check balance
    tool_pct = (stats.get('tool_use', 0) / total * 100) if total > 0 else 0
    direct_pct = (stats.get('direct_generation', 0) / total * 100) if total > 0 else 0
    multifile_pct = (stats.get('multi_file', 0) / total * 100) if total > 0 else 0

    print(f"Tool use: {tool_pct:.1f}% (target: 15%)")
    print(f"Direct generation: {direct_pct:.1f}% (target: 30%)")
    print(f"Multi-file: {multifile_pct:.1f}% (target: 12%)")

    if 10 <= tool_pct <= 20:
        print("✅ Tool use balanced (10-20%)")
    else:
        print("⚠️  Tool use out of range")

    if 25 <= direct_pct <= 35:
        print("✅ Direct generation balanced (25-35%)")
    else:
        print("⚠️  Direct generation out of range")

    if 10 <= multifile_pct <= 15:
        print("✅ Multi-file balanced (10-15%)")
    else:
        print("⚠️  Multi-file out of range")

    print("\n" + "=" * 60)
    print("✅ V15 Dataset Creation Complete!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Validate: python3 evaluation/finetuning/validate_v15_dataset.py")
    print(f"2. Train: Use {V15_FILE} for fine-tuning")
    print(f"3. Test: Run regression tests on all capabilities")

    return 0


if __name__ == '__main__':
    exit(main())

