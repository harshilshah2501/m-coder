#!/usr/bin/env python3
"""
Create V15 CORRECTED Dataset - Fixing all inconsistencies

INCONSISTENCIES FIXED:
1. Rename 'direct_generation' → 'code_edits' (they're edits, not generation)
2. Separate 'tool_use' into:
   - 'tool_calls' (10 examples with actual tool calls)
   - 'diff_generation' (390 examples with just diffs)
3. Standardize thinking tags:
   - All examples get <thinking> tags (not <thought>)
   - Add thinking blocks where missing
4. Ensure consistent format:
   - code_edits: SEARCH-REPLACE
   - single_file: SEARCH-REPLACE
   - multi_file: SEARCH-REPLACE
   - refactoring: SEARCH-REPLACE
   - file_creation: PLAIN CODE
   - tool_calls: AS-IS (preserve tool calls)
   - diff_generation: AS-IS (preserve diffs)
   - code_review: AS-IS
"""

import json
import re
from pathlib import Path
from typing import Dict

def standardize_thinking_block(content: str, category: str) -> str:
    """Standardize thinking blocks across all examples."""
    
    # If already has <thinking>, keep it
    if '<thinking>' in content and '</thinking>' in content:
        return content
    
    # If has <thought>, convert to <thinking>
    if '<thought>' in content:
        content = re.sub(r'<thought>(.*?)</thought>', r'<thinking>\1</thinking>', content, flags=re.DOTALL)
        return content
    
    # If missing thinking block, add a generic one
    if '<code>' in content:
        # Insert thinking before code block
        content = content.replace(
            '<code>',
            '<thinking>\nAnalyzing the required changes...\n</thinking>\n\n<code>'
        )
        return content
    
    # For AS-IS categories without code tags, add thinking at start
    if category in {'tool_calls', 'diff_generation', 'code_review'}:
        content = f'<thinking>\nProcessing request...\n</thinking>\n\n{content}'
    
    return content


def recategorize_example(example: Dict) -> Dict:
    """Recategorize and fix inconsistencies."""
    
    category = example.get('metadata', {}).get('category')
    content = example['messages'][-1]['content']
    
    # RENAME: direct_generation → code_edits
    if category == 'direct_generation':
        example['metadata']['category'] = 'code_edits'
        example['metadata']['original_category'] = 'direct_generation'
        category = 'code_edits'
    
    # SPLIT: tool_use → tool_calls or diff_generation
    if category == 'tool_use':
        if 'tool_calls' in content or ('"name":' in content and '"arguments":' in content):
            example['metadata']['category'] = 'tool_calls'
            example['metadata']['original_category'] = 'tool_use'
        else:
            example['metadata']['category'] = 'diff_generation'
            example['metadata']['original_category'] = 'tool_use'
    
    # STANDARDIZE: thinking blocks
    new_content = standardize_thinking_block(content, example['metadata']['category'])
    example['messages'][-1]['content'] = new_content
    
    return example


def main():
    """Main conversion process."""
    workspace_root = Path('/home/harshil/Harshil-PoCs')
    input_file = workspace_root / 'datasets' / 'archive' / 'v15_balanced_unified_diff_20251229.jsonl'
    output_file = workspace_root / 'datasets' / 'v15_corrected.jsonl'
    
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"\nFixing inconsistencies...")
    print("=" * 70)
    
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        return
    
    converted_count = 0
    category_stats = {}
    
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line_num, line in enumerate(f_in, 1):
            try:
                example = json.loads(line)
                corrected = recategorize_example(example)
                
                category = corrected.get('metadata', {}).get('category', 'unknown')
                category_stats[category] = category_stats.get(category, 0) + 1
                
                f_out.write(json.dumps(corrected) + '\n')
                converted_count += 1
                
                if converted_count % 500 == 0:
                    print(f"✓ Processed {converted_count} examples...")
            
            except Exception as e:
                print(f"⚠ ERROR on line {line_num}: {str(e)[:100]}")
                continue
    
    print("\n" + "=" * 70)
    print(f"✅ Correction Complete!")
    print(f"\nStatistics:")
    print(f"  Total examples: {converted_count}")
    print(f"\nNew Category Distribution:")
    for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        pct = (count / converted_count * 100) if converted_count > 0 else 0
        print(f"  {cat:20s}: {count:4d} ({pct:5.1f}%)")
    
    print(f"\nOutput file: {output_file}")
    print(f"File size: {output_file.stat().st_size / (1024*1024):.1f} MB")


if __name__ == '__main__':
    main()

