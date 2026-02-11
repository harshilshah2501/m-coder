#!/usr/bin/env python3
"""
Audit v12 training data to identify format issues.

This script analyzes v12_combined.jsonl to find:
1. Missing File: prefixes
2. Missing diff headers (--- a/ and +++ b/)
3. Incomplete hunks
4. Wrong language tags (```java vs ```diff)
5. Truncated outputs

Usage:
    python3 audit_v12_format.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


def check_diff_format(content: str) -> Dict[str, any]:
    """
    Check if content has proper unified diff format.
    
    Returns dict with:
        - has_file_prefix: bool
        - has_diff_headers: bool
        - has_hunks: bool
        - has_thinking: bool
        - has_code_wrapper: bool
        - language_tag: str (java, diff, python, etc.)
        - file_count: int
        - issues: List[str]
    """
    result = {
        'has_file_prefix': False,
        'has_diff_headers': False,
        'has_hunks': False,
        'has_thinking': False,
        'has_code_wrapper': False,
        'language_tag': None,
        'file_count': 0,
        'issues': []
    }
    
    # Check for <thinking> wrapper
    if '<thinking>' in content and '</thinking>' in content:
        result['has_thinking'] = True
    
    # Check for <code> wrapper
    if '<code>' in content and '</code>' in content:
        result['has_code_wrapper'] = True
    
    # Check for File: prefix
    file_matches = re.findall(r'File:\s*([^\n]+)', content)
    if file_matches:
        result['has_file_prefix'] = True
        result['file_count'] = len(file_matches)
    
    # Check for diff headers
    diff_header_matches = re.findall(r'---\s+a/([^\n]+)\n\+\+\+\s+b/([^\n]+)', content)
    if diff_header_matches:
        result['has_diff_headers'] = True
        if not result['has_file_prefix']:
            result['file_count'] = len(diff_header_matches)
    
    # Check for hunks
    hunk_matches = re.findall(r'@@\s+-\d+,\d+\s+\+\d+,\d+\s+@@', content)
    if hunk_matches:
        result['has_hunks'] = True
    
    # Check language tag
    lang_match = re.search(r'```(\w+)', content)
    if lang_match:
        result['language_tag'] = lang_match.group(1)
    
    # Identify issues
    if result['has_code_wrapper'] and not result['has_file_prefix']:
        result['issues'].append('Missing File: prefix')
    
    if result['has_hunks'] and not result['has_diff_headers']:
        result['issues'].append('Missing diff headers (--- a/ and +++ b/)')
    
    if result['has_hunks'] and result['language_tag'] != 'diff':
        result['issues'].append(f'Wrong language tag: ```{result["language_tag"]} (should be ```diff)')
    
    if result['has_code_wrapper'] and not result['has_hunks']:
        result['issues'].append('No hunks found (possibly full file replacement)')
    
    if not result['has_thinking']:
        result['issues'].append('Missing <thinking> wrapper')
    
    if not result['has_code_wrapper']:
        result['issues'].append('Missing <code> wrapper')
    
    return result


def audit_dataset(jsonl_path: Path) -> Dict[str, any]:
    """Audit entire dataset and return statistics."""
    
    stats = {
        'total_examples': 0,
        'with_file_prefix': 0,
        'with_diff_headers': 0,
        'with_hunks': 0,
        'with_thinking': 0,
        'with_code_wrapper': 0,
        'language_tags': defaultdict(int),
        'issues_count': defaultdict(int),
        'examples_with_issues': [],
        'file_count_distribution': defaultdict(int)
    }
    
    print(f"📂 Reading {jsonl_path}...")
    
    with open(jsonl_path, 'r') as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            
            try:
                example = json.loads(line)
                stats['total_examples'] += 1
                
                # Get assistant response
                messages = example.get('messages', [])
                assistant_msg = None
                for msg in messages:
                    if msg.get('role') == 'assistant':
                        assistant_msg = msg.get('content', '')
                        break
                
                if not assistant_msg:
                    stats['issues_count']['No assistant message'] += 1
                    continue
                
                # Check format
                check = check_diff_format(assistant_msg)
                
                if check['has_file_prefix']:
                    stats['with_file_prefix'] += 1
                if check['has_diff_headers']:
                    stats['with_diff_headers'] += 1
                if check['has_hunks']:
                    stats['with_hunks'] += 1
                if check['has_thinking']:
                    stats['with_thinking'] += 1
                if check['has_code_wrapper']:
                    stats['with_code_wrapper'] += 1
                
                if check['language_tag']:
                    stats['language_tags'][check['language_tag']] += 1
                
                stats['file_count_distribution'][check['file_count']] += 1
                
                # Track issues
                for issue in check['issues']:
                    stats['issues_count'][issue] += 1
                
                if check['issues']:
                    stats['examples_with_issues'].append({
                        'index': idx,
                        'issues': check['issues'],
                        'preview': assistant_msg[:200]
                    })
            
            except Exception as e:
                print(f"⚠️  Error processing line {idx}: {e}")
    
    return stats


def print_report(stats: Dict[str, any]):
    """Print audit report."""
    print("\n" + "="*80)
    print("📊 V12 TRAINING DATA AUDIT REPORT")
    print("="*80)

    total = stats['total_examples']
    print(f"\n📈 Overall Statistics:")
    print(f"   Total examples: {total}")
    print(f"   With <thinking> wrapper: {stats['with_thinking']} ({stats['with_thinking']/total*100:.1f}%)")
    print(f"   With <code> wrapper: {stats['with_code_wrapper']} ({stats['with_code_wrapper']/total*100:.1f}%)")

    print(f"\n🔍 Diff Format Compliance:")
    print(f"   With File: prefix: {stats['with_file_prefix']} ({stats['with_file_prefix']/total*100:.1f}%)")
    print(f"   With diff headers (--- a/): {stats['with_diff_headers']} ({stats['with_diff_headers']/total*100:.1f}%)")
    print(f"   With hunks (@@): {stats['with_hunks']} ({stats['with_hunks']/total*100:.1f}%)")

    print(f"\n🏷️  Language Tags:")
    for tag, count in sorted(stats['language_tags'].items(), key=lambda x: -x[1]):
        print(f"   ```{tag}: {count} ({count/total*100:.1f}%)")

    print(f"\n📁 File Count Distribution:")
    for file_count, count in sorted(stats['file_count_distribution'].items()):
        print(f"   {file_count} files: {count} examples")

    print(f"\n⚠️  Issues Found:")
    for issue, count in sorted(stats['issues_count'].items(), key=lambda x: -x[1]):
        print(f"   {issue}: {count} ({count/total*100:.1f}%)")

    print(f"\n🔴 Examples with Issues: {len(stats['examples_with_issues'])}")
    if stats['examples_with_issues']:
        print(f"\n   First 5 problematic examples:")
        for ex in stats['examples_with_issues'][:5]:
            print(f"\n   Example #{ex['index']}:")
            print(f"   Issues: {', '.join(ex['issues'])}")
            print(f"   Preview: {ex['preview']}...")

    print("\n" + "="*80)
    print("💡 Recommendations:")

    if stats['with_file_prefix'] < total * 0.9:
        print("   ❌ CRITICAL: Less than 90% have File: prefix - MUST FIX")

    if stats['with_diff_headers'] < total * 0.9:
        print("   ❌ CRITICAL: Less than 90% have diff headers - MUST FIX")

    if stats['language_tags'].get('diff', 0) < total * 0.8:
        print("   ⚠️  WARNING: Less than 80% use ```diff tag - SHOULD FIX")

    if stats['with_thinking'] < total * 0.95:
        print("   ⚠️  WARNING: Less than 95% have <thinking> wrapper - SHOULD FIX")

    print("="*80)


def main():
    """Main entry point."""
    import sys

    script_dir = Path(__file__).parent

    # Accept file path as argument
    if len(sys.argv) > 1:
        jsonl_path = Path(sys.argv[1])
    else:
        jsonl_path = script_dir / "v12_combined.jsonl"

    if not jsonl_path.exists():
        print(f"❌ Error: {jsonl_path} not found")
        return 1

    stats = audit_dataset(jsonl_path)
    print_report(stats)

    # Save detailed report
    report_name = jsonl_path.stem + "_audit_report.json"
    report_path = script_dir / report_name
    with open(report_path, 'w') as f:
        # Convert defaultdict to dict for JSON serialization
        stats_serializable = {
            'total_examples': stats['total_examples'],
            'with_file_prefix': stats['with_file_prefix'],
            'with_diff_headers': stats['with_diff_headers'],
            'with_hunks': stats['with_hunks'],
            'with_thinking': stats['with_thinking'],
            'with_code_wrapper': stats['with_code_wrapper'],
            'language_tags': dict(stats['language_tags']),
            'issues_count': dict(stats['issues_count']),
            'file_count_distribution': dict(stats['file_count_distribution']),
            'examples_with_issues': stats['examples_with_issues'][:20]  # Save first 20
        }
        json.dump(stats_serializable, f, indent=2)

    print(f"\n💾 Detailed report saved to: {report_path}")

    return 0


if __name__ == '__main__':
    exit(main())


