#!/usr/bin/env python3
"""
Reasoning Dataset Manager - All-in-one tool for creating and verifying reasoning datasets

Features:
1. Verify dataset format and quality
2. Show statistics and examples
3. Interactive review mode
4. Fix common issues
5. Export reports

Usage:
    # Verify dataset
    python reasoning_dataset_manager.py verify --input v13_combined.jsonl
    
    # Show statistics
    python reasoning_dataset_manager.py stats --input v13_combined.jsonl
    
    # Interactive review (sample 10 random examples)
    python reasoning_dataset_manager.py review --input v13_combined.jsonl --sample 10
    
    # Fix common issues
    python reasoning_dataset_manager.py fix --input v13_combined.jsonl --output v13_fixed.jsonl
    
    # Generate HTML report
    python reasoning_dataset_manager.py report --input v13_combined.jsonl --output report.html
"""

import json
import argparse
import random
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import re


class ReasoningDatasetManager:
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.examples = []
        self.load_examples()
    
    def load_examples(self):
        """Load examples from JSONL file"""
        print(f"📂 Loading {self.input_file}...")
        with open(self.input_file) as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        self.examples.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Line {line_num}: Invalid JSON - {e}")
        print(f"✅ Loaded {len(self.examples)} examples\n")
    
    def verify(self) -> Dict:
        """Verify dataset format and quality"""
        print("🔍 VERIFICATION REPORT")
        print("=" * 80)
        
        issues = defaultdict(list)
        stats = {
            'total': len(self.examples),
            'has_thinking': 0,
            'has_code': 0,
            'has_both': 0,
            'valid_format': 0,
            'avg_thinking_length': 0,
            'avg_code_length': 0,
        }
        
        thinking_lengths = []
        code_lengths = []
        
        for i, example in enumerate(self.examples):
            # Check structure
            if 'messages' not in example:
                issues['missing_messages'].append(i)
                continue
            
            messages = example['messages']
            if len(messages) < 2:
                issues['insufficient_messages'].append(i)
                continue
            
            # Find assistant message
            assistant_msg = next((m for m in messages if m['role'] == 'assistant'), None)
            if not assistant_msg:
                issues['no_assistant_message'].append(i)
                continue
            
            content = assistant_msg['content']
            
            # Check for XML tags
            has_thinking = '<thinking>' in content and '</thinking>' in content
            has_code = '<code>' in content and '</code>' in content
            
            if has_thinking:
                stats['has_thinking'] += 1
                # Extract thinking content
                match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
                if match:
                    thinking_lengths.append(len(match.group(1).strip()))
            
            if has_code:
                stats['has_code'] += 1
                # Extract code content
                match = re.search(r'<code>(.*?)</code>', content, re.DOTALL)
                if match:
                    code_lengths.append(len(match.group(1).strip()))
            
            if has_thinking and has_code:
                stats['has_both'] += 1
                stats['valid_format'] += 1
            elif not has_thinking and not has_code:
                issues['no_xml_tags'].append(i)
            elif not has_thinking:
                issues['missing_thinking'].append(i)
            elif not has_code:
                issues['missing_code'].append(i)
        
        # Calculate averages
        if thinking_lengths:
            stats['avg_thinking_length'] = sum(thinking_lengths) / len(thinking_lengths)
        if code_lengths:
            stats['avg_code_length'] = sum(code_lengths) / len(code_lengths)
        
        # Print results
        print(f"Total examples: {stats['total']}")
        print(f"Valid format (has both <thinking> and <code>): {stats['valid_format']} ({stats['valid_format']/stats['total']*100:.1f}%)")
        print(f"Has <thinking> tag: {stats['has_thinking']} ({stats['has_thinking']/stats['total']*100:.1f}%)")
        print(f"Has <code> tag: {stats['has_code']} ({stats['has_code']/stats['total']*100:.1f}%)")
        print(f"Average thinking length: {stats['avg_thinking_length']:.0f} chars")
        print(f"Average code length: {stats['avg_code_length']:.0f} chars")
        
        print("\n📊 ISSUES FOUND:")
        if not issues:
            print("✅ No issues found!")
        else:
            for issue_type, indices in issues.items():
                print(f"  {issue_type}: {len(indices)} examples")
                if len(indices) <= 5:
                    print(f"    Indices: {indices}")
                else:
                    print(f"    Indices: {indices[:5]} ... (and {len(indices)-5} more)")
        
        print("=" * 80)
        return stats, issues
    
    def show_stats(self):
        """Show detailed statistics"""
        stats, issues = self.verify()
        
        print("\n📈 DETAILED STATISTICS")
        print("=" * 80)
        
        # Analyze reasoning structure
        problem_count = 0
        plan_count = 0
        edge_cases_count = 0
        
        for example in self.examples:
            assistant_msg = next((m for m in example.get('messages', []) if m['role'] == 'assistant'), None)
            if not assistant_msg:
                continue
            
            content = assistant_msg['content']
            if '**Problem**' in content or 'Problem:' in content:
                problem_count += 1
            if '**Plan**' in content or 'Plan:' in content:
                plan_count += 1
            if '**Edge Cases**' in content or 'Edge Cases:' in content:
                edge_cases_count += 1
        
        print(f"Reasoning structure:")
        print(f"  Has 'Problem' section: {problem_count} ({problem_count/len(self.examples)*100:.1f}%)")
        print(f"  Has 'Plan' section: {plan_count} ({plan_count/len(self.examples)*100:.1f}%)")
        print(f"  Has 'Edge Cases' section: {edge_cases_count} ({edge_cases_count/len(self.examples)*100:.1f}%)")
        print("=" * 80)

    def review_samples(self, num_samples: int = 10):
        """Interactive review of random samples"""
        print(f"\n🔍 INTERACTIVE REVIEW ({num_samples} random samples)")
        print("=" * 80)

        if num_samples > len(self.examples):
            num_samples = len(self.examples)

        samples = random.sample(self.examples, num_samples)

        for i, example in enumerate(samples, 1):
            print(f"\n{'='*80}")
            print(f"SAMPLE {i}/{num_samples}")
            print(f"{'='*80}")

            messages = example.get('messages', [])
            user_msg = next((m for m in messages if m['role'] == 'user'), None)
            assistant_msg = next((m for m in messages if m['role'] == 'assistant'), None)

            if user_msg:
                print("\n📝 USER PROMPT:")
                print("-" * 80)
                print(user_msg['content'][:500])
                if len(user_msg['content']) > 500:
                    print("... (truncated)")

            if assistant_msg:
                content = assistant_msg['content']

                # Extract thinking
                thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
                if thinking_match:
                    print("\n💭 THINKING:")
                    print("-" * 80)
                    print(thinking_match.group(1).strip())

                # Extract code
                code_match = re.search(r'<code>(.*?)</code>', content, re.DOTALL)
                if code_match:
                    print("\n💻 CODE:")
                    print("-" * 80)
                    code_content = code_match.group(1).strip()
                    print(code_content[:800])
                    if len(code_content) > 800:
                        print("... (truncated)")

                # Check for issues
                issues = []
                if not thinking_match:
                    issues.append("❌ Missing <thinking> tag")
                if not code_match:
                    issues.append("❌ Missing <code> tag")

                if issues:
                    print("\n⚠️  ISSUES:")
                    for issue in issues:
                        print(f"  {issue}")
                else:
                    print("\n✅ Format looks good")

            # Ask for feedback
            print("\n" + "-" * 80)
            feedback = input("Rate this example (1-5, or 's' to skip): ").strip()
            if feedback.isdigit():
                print(f"Recorded rating: {feedback}/5")
            print()

    def fix_common_issues(self, output_file: str):
        """Fix common formatting issues"""
        print("\n🔧 FIXING COMMON ISSUES")
        print("=" * 80)

        fixed_count = 0
        fixed_examples = []

        for i, example in enumerate(self.examples):
            messages = example.get('messages', [])
            assistant_msg = next((m for m in messages if m['role'] == 'assistant'), None)

            if not assistant_msg:
                fixed_examples.append(example)
                continue

            content = assistant_msg['content']
            original_content = content

            # Fix 1: Add missing <code> tags if content looks like code
            if '<thinking>' in content and '</thinking>' in content and '<code>' not in content:
                # Extract thinking
                thinking_match = re.search(r'<thinking>.*?</thinking>', content, re.DOTALL)
                if thinking_match:
                    thinking = thinking_match.group(0)
                    code = content.replace(thinking, '').strip()
                    if code:
                        content = f"{thinking}\n\n<code>\n{code}\n</code>"
                        fixed_count += 1

            # Fix 2: Add missing <thinking> tags if only code exists
            elif '<code>' in content and '</code>' in content and '<thinking>' not in content:
                code_match = re.search(r'<code>.*?</code>', content, re.DOTALL)
                if code_match:
                    code = code_match.group(0)
                    # Add minimal thinking
                    content = f"<thinking>\n**Problem**: Implementing requested changes\n**Plan**: Apply the code modifications\n</thinking>\n\n{code}"
                    fixed_count += 1

            # Fix 3: Wrap bare code in tags
            elif '<thinking>' not in content and '<code>' not in content:
                # Assume it's all code
                content = f"<thinking>\n**Problem**: Implementing requested changes\n**Plan**: Apply the code modifications\n</thinking>\n\n<code>\n{content}\n</code>"
                fixed_count += 1

            # Update message
            if content != original_content:
                assistant_msg['content'] = content

            fixed_examples.append(example)

        # Save fixed examples
        print(f"Fixed {fixed_count} examples")
        print(f"Saving to {output_file}...")

        with open(output_file, 'w') as f:
            for example in fixed_examples:
                f.write(json.dumps(example) + '\n')

        print(f"✅ Saved {len(fixed_examples)} examples to {output_file}")
        print("=" * 80)

    def generate_html_report(self, output_file: str):
        """Generate HTML report with examples"""
        print(f"\n📄 GENERATING HTML REPORT: {output_file}")
        print("=" * 80)

        stats, issues = self.verify()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Reasoning Dataset Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; }}
        h1 {{ color: #333; }}
        .stats {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .stat-item {{ margin: 10px 0; }}
        .example {{ border: 1px solid #ddd; margin: 20px 0; padding: 15px; border-radius: 5px; }}
        .thinking {{ background: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
        .code {{ background: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #28a745; font-family: monospace; white-space: pre-wrap; }}
        .issue {{ color: #dc3545; }}
        .success {{ color: #28a745; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Reasoning Dataset Report</h1>
        <p>Generated from: {self.input_file}</p>

        <div class="stats">
            <h2>Statistics</h2>
            <div class="stat-item">Total examples: <strong>{stats['total']}</strong></div>
            <div class="stat-item">Valid format: <strong>{stats['valid_format']}</strong> ({stats['valid_format']/stats['total']*100:.1f}%)</div>
            <div class="stat-item">Has thinking: <strong>{stats['has_thinking']}</strong> ({stats['has_thinking']/stats['total']*100:.1f}%)</div>
            <div class="stat-item">Has code: <strong>{stats['has_code']}</strong> ({stats['has_code']/stats['total']*100:.1f}%)</div>
            <div class="stat-item">Avg thinking length: <strong>{stats['avg_thinking_length']:.0f}</strong> chars</div>
            <div class="stat-item">Avg code length: <strong>{stats['avg_code_length']:.0f}</strong> chars</div>
        </div>
"""

        # Add sample examples
        html += "<h2>Sample Examples (first 5)</h2>"
        for i, example in enumerate(self.examples[:5]):
            messages = example.get('messages', [])
            user_msg = next((m for m in messages if m['role'] == 'user'), None)
            assistant_msg = next((m for m in messages if m['role'] == 'assistant'), None)

            html += f'<div class="example"><h3>Example {i+1}</h3>'

            if user_msg:
                html += f'<p><strong>Prompt:</strong></p><p>{user_msg["content"][:300]}...</p>'

            if assistant_msg:
                content = assistant_msg['content']
                thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
                code_match = re.search(r'<code>(.*?)</code>', content, re.DOTALL)

                if thinking_match:
                    html += f'<div class="thinking"><strong>Thinking:</strong><br>{thinking_match.group(1).strip()[:500]}...</div>'
                if code_match:
                    html += f'<div class="code"><strong>Code:</strong><br>{code_match.group(1).strip()[:500]}...</div>'

            html += '</div>'

        html += """
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html)

        print(f"✅ Report saved to {output_file}")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Reasoning Dataset Manager")
    parser.add_argument('command', choices=['verify', 'stats', 'review', 'fix', 'report'],
                       help='Command to run')
    parser.add_argument('--input', required=True, help='Input JSONL file')
    parser.add_argument('--output', help='Output file (for fix/report commands)')
    parser.add_argument('--sample', type=int, default=10, help='Number of samples for review')

    args = parser.parse_args()

    manager = ReasoningDatasetManager(args.input)

    if args.command == 'verify':
        manager.verify()
    elif args.command == 'stats':
        manager.show_stats()
    elif args.command == 'review':
        manager.review_samples(args.sample)
    elif args.command == 'fix':
        if not args.output:
            print("Error: --output required for fix command")
            return
        manager.fix_common_issues(args.output)
    elif args.command == 'report':
        if not args.output:
            print("Error: --output required for report command")
            return
        manager.generate_html_report(args.output)


if __name__ == '__main__':
    main()


