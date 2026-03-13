#!/usr/bin/env python3
"""
Verify and Analyze Extracted Fine-Tuning Data

Run this on the GPU machine after copying the JSONL file.

Usage:
    python verify_extracted_data.py --input motadata_finetuning_data.jsonl
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List


def load_jsonl(path: str) -> List[dict]:
    """Load JSONL file."""
    examples = []
    with open(path) as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def validate_example(example: dict) -> tuple:
    """Validate a single training example."""
    issues = []
    
    messages = example.get('messages', [])
    metadata = example.get('metadata', {})
    
    # Check message structure
    if len(messages) != 3:
        issues.append("Missing messages (need system, user, assistant)")
        return False, issues
    
    system_msg = messages[0].get('content', '')
    user_msg = messages[1].get('content', '')
    assistant_msg = messages[2].get('content', '')
    
    # Check system prompt
    if len(system_msg) < 10:
        issues.append("System prompt too short")
    
    # Check user message has file content
    if 'File:' not in user_msg:
        issues.append("User message missing 'File:' header")
    if 'Content:' not in user_msg:
        issues.append("User message missing 'Content:' section")
    if 'Task:' not in user_msg:
        issues.append("User message missing 'Task:' (commit message)")
    
    # Check assistant message has diff
    if '```diff' not in assistant_msg:
        issues.append("Assistant message missing diff block")
    if '--- ' not in assistant_msg:
        issues.append("Diff missing '---' header")
    if '+++ ' not in assistant_msg:
        issues.append("Diff missing '+++' header")
    if '@@ ' not in assistant_msg:
        issues.append("Diff missing '@@ ' hunk header")
    
    # Check metadata
    if not metadata.get('repo'):
        issues.append("Missing repo in metadata")
    if not metadata.get('commit'):
        issues.append("Missing commit in metadata")
    if not metadata.get('file'):
        issues.append("Missing file in metadata")
    
    return len(issues) == 0, issues


def analyze_data(examples: List[dict]) -> dict:
    """Analyze the extracted data."""
    stats = {
        'total_examples': len(examples),
        'valid_examples': 0,
        'invalid_examples': 0,
        'repos': Counter(),
        'file_extensions': Counter(),
        'hunks_distribution': Counter(),
        'lines_added_total': 0,
        'lines_removed_total': 0,
        'avg_diff_size': 0,
        'issues': defaultdict(int),
    }
    
    valid_count = 0
    total_diff_size = 0
    
    for ex in examples:
        is_valid, issues = validate_example(ex)
        
        if is_valid:
            stats['valid_examples'] += 1
            valid_count += 1
        else:
            stats['invalid_examples'] += 1
            for issue in issues:
                stats['issues'][issue] += 1
        
        metadata = ex.get('metadata', {})
        
        # Count by repo
        repo = metadata.get('repo', 'unknown')
        stats['repos'][repo] += 1
        
        # Count by extension
        file_path = metadata.get('file', '')
        ext = Path(file_path).suffix or 'no_extension'
        stats['file_extensions'][ext] += 1
        
        # Hunks
        hunks = metadata.get('hunks', 0)
        stats['hunks_distribution'][hunks] += 1
        
        # Lines
        stats['lines_added_total'] += metadata.get('lines_added', 0)
        stats['lines_removed_total'] += metadata.get('lines_removed', 0)
        
        # Diff size
        assistant_msg = ex.get('messages', [{}])[-1].get('content', '')
        total_diff_size += len(assistant_msg)
    
    if valid_count > 0:
        stats['avg_diff_size'] = total_diff_size // valid_count
    
    return stats


def print_report(stats: dict):
    """Print analysis report."""
    print("\n" + "="*70)
    print("FINE-TUNING DATA VERIFICATION REPORT")
    print("="*70)
    
    print(f"\n📊 OVERVIEW")
    print(f"   Total examples: {stats['total_examples']}")
    print(f"   Valid examples: {stats['valid_examples']} ({100*stats['valid_examples']//max(1,stats['total_examples'])}%)")
    print(f"   Invalid examples: {stats['invalid_examples']}")
    
    print(f"\n📁 BY REPOSITORY")
    for repo, count in stats['repos'].most_common():
        print(f"   {repo}: {count}")
    
    print(f"\n📝 BY FILE TYPE")
    for ext, count in stats['file_extensions'].most_common(10):
        print(f"   {ext}: {count}")
    
    print(f"\n📐 DIFF STATISTICS")
    print(f"   Total lines added: {stats['lines_added_total']}")
    print(f"   Total lines removed: {stats['lines_removed_total']}")
    print(f"   Average diff size: {stats['avg_diff_size']} bytes")
    
    print(f"\n🔢 HUNKS DISTRIBUTION")
    for hunks, count in sorted(stats['hunks_distribution'].items()):
        print(f"   {hunks} hunks: {count} examples")
    
    if stats['issues']:
        print(f"\n⚠️ ISSUES FOUND")
        for issue, count in stats['issues'].items():
            print(f"   {issue}: {count}")
    
    print("\n" + "="*70)
    
    # Final verdict
    if stats['valid_examples'] >= 500:
        print("✅ TARGET ACHIEVED: 500+ valid examples")
    elif stats['valid_examples'] >= 200:
        print("⚠️ MINIMUM MET: 200+ examples (consider adding more)")
    else:
        print("❌ INSUFFICIENT: Need more examples for effective fine-tuning")
    
    print("="*70)


def main():
    parser = argparse.ArgumentParser(description='Verify extracted fine-tuning data')
    parser.add_argument('--input', required=True, help='Input JSONL file')
    parser.add_argument('--sample', type=int, default=3, help='Number of samples to show')
    args = parser.parse_args()
    
    print(f"Loading {args.input}...")
    examples = load_jsonl(args.input)
    print(f"Loaded {len(examples)} examples")
    
    stats = analyze_data(examples)
    print_report(stats)
    
    # Show samples
    if args.sample > 0 and examples:
        print(f"\n📋 SAMPLE EXAMPLES (first {args.sample})")
        print("-"*70)
        for i, ex in enumerate(examples[:args.sample]):
            meta = ex.get('metadata', {})
            print(f"\nExample {i+1}:")
            print(f"  Repo: {meta.get('repo')}")
            print(f"  Commit: {meta.get('commit')}")
            print(f"  File: {meta.get('file')}")
            print(f"  Hunks: {meta.get('hunks')}, Lines: +{meta.get('lines_added')}/-{meta.get('lines_removed')}")


if __name__ == '__main__':
    main()

