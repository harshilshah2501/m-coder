#!/usr/bin/env python3
"""
Validate completeness of model-generated code/diffs.

This script helps diagnose truncation issues (Challenge #2).

Usage:
    python validate_output.py --file generated_output.txt
    python validate_output.py --log generation_log.jsonl --stats
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


def is_complete_diff(output: str) -> Tuple[bool, List[str]]:
    """
    Check if a unified diff is complete.
    
    Returns:
        (is_complete, list_of_issues)
    """
    issues = []
    
    # Check 1: Balanced @@ markers (each hunk has start and end)
    hunk_markers = output.count('@@')
    if hunk_markers % 2 != 0:
        issues.append(f"Unbalanced hunk markers: {hunk_markers} @@ found (should be even)")
    
    # Check 2: Proper ending (not mid-line)
    stripped = output.rstrip()
    if stripped and not stripped.endswith(('\n', '---', '+++', ' ', '-', '+')):
        issues.append(f"Abrupt ending: last char is '{stripped[-1]}' (ord {ord(stripped[-1])})")
    
    # Check 3: Balanced braces in added code
    added_lines = [line[1:] for line in output.split('\n') if line.startswith('+') and not line.startswith('+++')]
    added_code = '\n'.join(added_lines)
    
    open_braces = added_code.count('{')
    close_braces = added_code.count('}')
    if open_braces != close_braces:
        issues.append(f"Unbalanced braces in added code: {open_braces} {{ vs {close_braces} }}")
    
    # Check 4: Balanced parentheses in added code
    open_parens = added_code.count('(')
    close_parens = added_code.count(')')
    if open_parens != close_parens:
        issues.append(f"Unbalanced parentheses in added code: {open_parens} ( vs {close_parens} )")
    
    # Check 5: No incomplete hunks (hunk header without content)
    hunks = re.findall(r'@@.*?@@', output)
    for i, hunk_header in enumerate(hunks):
        # Find content after this hunk header
        hunk_start = output.find(hunk_header) + len(hunk_header)
        next_hunk = output.find('@@', hunk_start)
        
        if next_hunk == -1:
            # Last hunk - check if there's content
            content = output[hunk_start:].strip()
        else:
            content = output[hunk_start:next_hunk].strip()
        
        if not content or len(content) < 10:
            issues.append(f"Hunk {i+1} appears empty or too short")
    
    return len(issues) == 0, issues


def is_complete_code(output: str, language: str = "java") -> Tuple[bool, List[str]]:
    """
    Check if generated code is complete (not truncated).
    """
    issues = []
    
    # Check 1: Balanced braces
    if language in ["java", "javascript", "c", "cpp", "go"]:
        open_braces = output.count('{')
        close_braces = output.count('}')
        if open_braces != close_braces:
            issues.append(f"Unbalanced braces: {open_braces} {{ vs {close_braces} }}")
    
    # Check 2: Balanced parentheses
    open_parens = output.count('(')
    close_parens = output.count(')')
    if open_parens != close_parens:
        issues.append(f"Unbalanced parentheses: {open_parens} ( vs {close_parens} )")
    
    # Check 3: No incomplete strings
    # Simple check: count quotes (should be even)
    double_quotes = output.count('"') - output.count('\\"')
    if double_quotes % 2 != 0:
        issues.append(f"Unbalanced double quotes: {double_quotes}")
    
    # Check 4: Ends properly (not mid-statement)
    stripped = output.rstrip()
    if language == "java":
        # Java should end with } or ;
        if stripped and not stripped.endswith(('}', ';', '//', '*/')):
            issues.append(f"Unexpected ending for Java code: '{stripped[-20:]}'")
    
    # Check 5: No truncation markers
    truncation_markers = ['...', '<truncated>', '[TRUNCATED]', '# ...']
    for marker in truncation_markers:
        if marker in output:
            issues.append(f"Found truncation marker: '{marker}'")
    
    return len(issues) == 0, issues


def analyze_file(file_path: str, output_type: str = "auto") -> Dict:
    """Analyze a single output file"""
    with open(file_path) as f:
        content = f.read()
    
    # Auto-detect type
    if output_type == "auto":
        if content.startswith('---') or '@@' in content:
            output_type = "diff"
        else:
            output_type = "code"
    
    if output_type == "diff":
        is_complete, issues = is_complete_diff(content)
    else:
        is_complete, issues = is_complete_code(content)
    
    return {
        "file": file_path,
        "type": output_type,
        "is_complete": is_complete,
        "issues": issues,
        "length": len(content),
        "lines": content.count('\n')
    }


def analyze_log(log_path: str) -> Dict:
    """Analyze a JSONL log file with multiple generations"""
    results = {
        "total": 0,
        "complete": 0,
        "truncated": 0,
        "examples": []
    }
    
    with open(log_path) as f:
        for line in f:
            if not line.strip():
                continue
            
            data = json.loads(line)
            output = data.get("generated_text", data.get("output", ""))
            
            # Detect type
            if output.startswith('---') or '@@' in output:
                is_complete, issues = is_complete_diff(output)
            else:
                is_complete, issues = is_complete_code(output)
            
            results["total"] += 1
            if is_complete:
                results["complete"] += 1
            else:
                results["truncated"] += 1
                results["examples"].append({
                    "index": results["total"],
                    "issues": issues,
                    "length": len(output),
                    "preview": output[:200] + "..." if len(output) > 200 else output
                })
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Validate model output completeness")
    parser.add_argument("--file", help="Single output file to validate")
    parser.add_argument("--log", help="JSONL log file with multiple outputs")
    parser.add_argument("--type", choices=["auto", "diff", "code"], default="auto",
                       help="Type of output (auto-detect by default)")
    parser.add_argument("--stats", action="store_true", help="Show statistics for log file")
    
    args = parser.parse_args()
    
    if args.file:
        result = analyze_file(args.file, args.type)
        print(f"File: {result['file']}")
        print(f"Type: {result['type']}")
        print(f"Length: {result['length']} chars, {result['lines']} lines")
        print(f"Complete: {'✅ YES' if result['is_complete'] else '❌ NO'}")
        
        if result['issues']:
            print("\nIssues found:")
            for issue in result['issues']:
                print(f"  - {issue}")
        else:
            print("\nNo issues found!")
    
    elif args.log:
        results = analyze_log(args.log)
        
        print(f"Analyzed {results['total']} outputs")
        print(f"Complete: {results['complete']} ({results['complete']/results['total']*100:.1f}%)")
        print(f"Truncated: {results['truncated']} ({results['truncated']/results['total']*100:.1f}%)")
        
        if args.stats and results['examples']:
            print(f"\nTruncated examples:")
            for ex in results['examples'][:10]:  # Show first 10
                print(f"\n  Example {ex['index']} ({ex['length']} chars):")
                for issue in ex['issues']:
                    print(f"    - {issue}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

