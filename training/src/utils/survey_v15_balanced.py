#!/usr/bin/env python3
"""
Comprehensive survey of v15_balanced.jsonl dataset.
Categorize examples by pattern type to enable group-by-group conversion.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

INPUT_FILE = Path("v15_balanced.jsonl")
OUTPUT_REPORT = Path("v15_balanced_survey_report.json")


def analyze_example(example: Dict, index: int) -> Dict:
    """Analyze a single example and categorize it."""
    messages = example.get('messages', [])
    
    analysis = {
        'index': index,
        'message_count': len(messages),
        'has_system': False,
        'has_user': False,
        'has_assistant': False,
        'has_tool': False,
        'has_tool_calls': False,
        'has_thinking': False,
        'has_code': False,
        'has_diff': False,
        'has_search_replace': False,
        'pattern': 'unknown',
        'file_count': 0,
        'assistant_length': 0,
    }
    
    # Analyze messages
    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        if role == 'system':
            analysis['has_system'] = True
        elif role == 'user':
            analysis['has_user'] = True
        elif role == 'assistant':
            analysis['has_assistant'] = True
            analysis['assistant_length'] = len(content)
            
            # Check for patterns in assistant message
            if '<thinking>' in content:
                analysis['has_thinking'] = True
            if '<code>' in content:
                analysis['has_code'] = True
            if 'diff --git' in content or '+++' in content or '---' in content:
                analysis['has_diff'] = True
            if '<<<< SEARCH' in content and '>>>> REPLACE' in content:
                analysis['has_search_replace'] = True
            if 'tool_calls' in content or '"name":' in content:
                analysis['has_tool_calls'] = True
            
            # Count files in diff
            file_markers = re.findall(r'diff --git|File:', content)
            analysis['file_count'] = len(file_markers)
            
        elif role == 'tool':
            analysis['has_tool'] = True
    
    # Determine pattern type
    if analysis['has_tool'] or analysis['has_tool_calls']:
        analysis['pattern'] = 'tool_use'
    elif analysis['has_search_replace']:
        analysis['pattern'] = 'search_replace'
    elif analysis['has_diff'] and analysis['has_code']:
        if analysis['file_count'] > 1:
            analysis['pattern'] = 'multi_file_diff'
        else:
            analysis['pattern'] = 'single_file_diff'
    elif analysis['has_code']:
        analysis['pattern'] = 'direct_code'
    elif analysis['has_thinking']:
        analysis['pattern'] = 'thinking_only'
    else:
        analysis['pattern'] = 'other'
    
    return analysis


def main():
    print("=" * 80)
    print("V15 Balanced Dataset Survey")
    print("=" * 80)
    print(f"Input: {INPUT_FILE}")
    print()
    
    if not INPUT_FILE.exists():
        print(f"❌ Error: {INPUT_FILE} not found!")
        return 1
    
    # Load examples
    print("Loading examples...")
    examples = []
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    
    print(f"✅ Loaded {len(examples)} examples\n")
    
    # Analyze all examples
    print("Analyzing examples...")
    analyses = []
    for i, example in enumerate(examples):
        if (i + 1) % 500 == 0:
            print(f"  Progress: {i + 1}/{len(examples)}")
        analyses.append(analyze_example(example, i))
    
    print(f"✅ Analyzed {len(analyses)} examples\n")
    
    # Group by pattern
    pattern_groups = defaultdict(list)
    for analysis in analyses:
        pattern_groups[analysis['pattern']].append(analysis)
    
    # Statistics
    print("=" * 80)
    print("PATTERN DISTRIBUTION")
    print("=" * 80)
    
    total = len(analyses)
    for pattern in sorted(pattern_groups.keys(), key=lambda p: len(pattern_groups[p]), reverse=True):
        count = len(pattern_groups[pattern])
        pct = (count / total) * 100
        print(f"{pattern:25s} {count:5d} ({pct:5.1f}%)")
    
    print(f"{'TOTAL':25s} {total:5d} (100.0%)")
    
    # Detailed breakdown
    print("\n" + "=" * 80)
    print("DETAILED BREAKDOWN BY PATTERN")
    print("=" * 80)
    
    for pattern in sorted(pattern_groups.keys()):
        group = pattern_groups[pattern]
        print(f"\n{pattern.upper()} ({len(group)} examples)")
        print("-" * 80)
        
        # Sample indices
        sample_indices = [a['index'] for a in group[:5]]
        print(f"Sample indices: {sample_indices}")
        
        # Statistics
        has_thinking = sum(1 for a in group if a['has_thinking'])
        has_code = sum(1 for a in group if a['has_code'])
        has_tool = sum(1 for a in group if a['has_tool'])
        avg_length = sum(a['assistant_length'] for a in group) / len(group) if group else 0
        avg_files = sum(a['file_count'] for a in group) / len(group) if group else 0
        
        print(f"  Has <thinking>: {has_thinking}/{len(group)} ({has_thinking/len(group)*100:.1f}%)")
        print(f"  Has <code>: {has_code}/{len(group)} ({has_code/len(group)*100:.1f}%)")
        print(f"  Has tool messages: {has_tool}/{len(group)} ({has_tool/len(group)*100:.1f}%)")
        print(f"  Avg assistant length: {avg_length:.0f} chars")
        print(f"  Avg file count: {avg_files:.1f}")
    
    # Save detailed report
    report = {
        'total_examples': total,
        'pattern_distribution': {
            pattern: len(group) for pattern, group in pattern_groups.items()
        },
        'pattern_details': {
            pattern: {
                'count': len(group),
                'sample_indices': [a['index'] for a in group[:10]],
                'has_thinking': sum(1 for a in group if a['has_thinking']),
                'has_code': sum(1 for a in group if a['has_code']),
                'has_tool': sum(1 for a in group if a['has_tool']),
                'avg_length': sum(a['assistant_length'] for a in group) / len(group) if group else 0,
                'avg_files': sum(a['file_count'] for a in group) / len(group) if group else 0,
            }
            for pattern, group in pattern_groups.items()
        },
        'all_analyses': analyses
    }
    
    print(f"\n\nSaving detailed report to {OUTPUT_REPORT}...")
    with open(OUTPUT_REPORT, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report saved!")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Review the pattern distribution above")
    print("2. Check sample examples for each pattern")
    print("3. Create group-specific conversion strategies")
    print("4. Convert each group with appropriate logic")
    
    return 0


if __name__ == '__main__':
    exit(main())

