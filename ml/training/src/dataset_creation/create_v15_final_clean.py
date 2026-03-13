#!/usr/bin/env python3
"""
Final Dataset Cleanup - Remove duplicates and fix remaining issues

Issues to fix:
1. Remove 129 duplicate examples
2. Add missing <thinking> tags to 4 file_creation examples
3. Ensure 100% format consistency
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Set
import re


def add_missing_thinking(content: str, category: str) -> str:
    """Add thinking block if missing."""
    if '<thinking>' in content and '</thinking>' in content:
        return content
    
    # Add thinking block at the start
    if category == 'file_creation':
        thinking = "<thinking>\nCreating new file with required implementation.\n</thinking>\n\n"
    else:
        thinking = "<thinking>\nAnalyzing the required changes.\n</thinking>\n\n"
    
    return thinking + content


def main():
    workspace_root = Path('/home/harshil/Harshil-PoCs')
    input_file = workspace_root / 'datasets' / 'v15_gold.jsonl'
    output_file = workspace_root / 'datasets' / 'v15_final.jsonl'
    
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"\nCleaning dataset...")
    print("=" * 70)
    
    seen_hashes: Set[str] = set()
    duplicates_removed = 0
    thinking_added = 0
    total_written = 0
    
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line_num, line in enumerate(f_in, 1):
            try:
                example = json.loads(line)
                content = example['messages'][-1]['content']
                category = example.get('metadata', {}).get('category', 'unknown')
                
                # Check for duplicates
                content_hash = hashlib.md5(content.encode()).hexdigest()
                if content_hash in seen_hashes:
                    duplicates_removed += 1
                    continue
                seen_hashes.add(content_hash)
                
                # Add missing thinking tags
                if '<thinking>' not in content:
                    content = add_missing_thinking(content, category)
                    example['messages'][-1]['content'] = content
                    thinking_added += 1
                
                # Write cleaned example
                f_out.write(json.dumps(example) + '\n')
                total_written += 1
                
                if total_written % 500 == 0:
                    print(f"✓ Processed {total_written} examples...")
            
            except Exception as e:
                print(f"⚠ ERROR on line {line_num}: {str(e)[:100]}")
                continue
    
    print("\n" + "=" * 70)
    print(f"✅ Cleanup Complete!")
    print(f"\nChanges:")
    print(f"  Duplicates removed: {duplicates_removed}")
    print(f"  Thinking tags added: {thinking_added}")
    print(f"  Total examples written: {total_written}")
    print(f"\nOutput file: {output_file}")
    print(f"File size: {output_file.stat().st_size / (1024*1024):.1f} MB")


if __name__ == '__main__':
    main()

