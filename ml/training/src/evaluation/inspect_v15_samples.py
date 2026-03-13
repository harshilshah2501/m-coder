#!/usr/bin/env python3
"""
Inspect sample examples from each pattern group in v15_balanced.jsonl
"""

import json
from pathlib import Path
from typing import Dict

INPUT_FILE = Path("v15_balanced.jsonl")
REPORT_FILE = Path("v15_balanced_survey_report.json")


def show_example(example: Dict, index: int, pattern: str):
    """Display a single example in readable format."""
    print(f"\n{'=' * 80}")
    print(f"Example #{index} - Pattern: {pattern}")
    print('=' * 80)
    
    messages = example.get('messages', [])
    
    for i, msg in enumerate(messages):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        
        print(f"\n[Message {i+1}] Role: {role}")
        print('-' * 80)
        
        # Truncate long content
        if len(content) > 1500:
            print(content[:750])
            print(f"\n... [TRUNCATED - {len(content)} total chars] ...\n")
            print(content[-750:])
        else:
            print(content)


def main():
    print("=" * 80)
    print("V15 Balanced Dataset - Sample Inspection")
    print("=" * 80)
    
    # Load report
    with open(REPORT_FILE, 'r') as f:
        report = json.load(f)
    
    # Load examples
    examples = []
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    
    print(f"Loaded {len(examples)} examples\n")
    
    # Show samples from each pattern
    patterns_to_inspect = [
        ('single_file_diff', 1),      # Most common convertible
        ('multi_file_diff', 1),       # Multi-file convertible
        ('tool_use', 1),              # Tool use pattern
        ('direct_code', 1),           # Direct code generation
        ('thinking_only', 1),         # Thinking without code
        ('other', 1),                 # Unknown pattern
    ]
    
    for pattern, count in patterns_to_inspect:
        if pattern in report['pattern_details']:
            sample_indices = report['pattern_details'][pattern]['sample_indices'][:count]
            
            for idx in sample_indices:
                if idx < len(examples):
                    show_example(examples[idx], idx, pattern)
    
    print("\n" + "=" * 80)
    print("Inspection complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()

