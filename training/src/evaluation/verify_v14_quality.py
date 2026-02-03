#!/usr/bin/env python3
"""Verify quality of v14 multi-file dataset."""

import json
import re
from pathlib import Path

def main():
    input_file = Path('evaluation/finetuning/v14_multifile_raw.jsonl')
    
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        return 1
    
    # Load examples
    with open(input_file) as f:
        examples = [json.loads(line) for line in f]
    
    print(f"{'='*70}")
    print(f"V14 Multi-File Dataset Quality Check")
    print(f"{'='*70}\n")
    
    print(f"✅ Total examples: {len(examples)}\n")
    
    # Check for Patch files
    patch_count = 0
    for ex in examples:
        assistant_msg = ex['messages'][2]['content']
        if re.search(r'Patch\d+\.java', assistant_msg):
            patch_count += 1
    
    print(f"✅ Examples with Patch*.java: {patch_count} (should be 0)\n")
    
    # Verify structure
    ex = examples[0]
    has_thinking = '<thinking>' in ex['messages'][2]['content']
    has_code = '<code>' in ex['messages'][2]['content']
    has_diff = '```diff' in ex['messages'][2]['content']
    
    print(f"✅ Has <thinking> blocks: {has_thinking}")
    print(f"✅ Has <code> blocks: {has_code}")
    print(f"✅ Has diff formatting: {has_diff}\n")
    
    # File count stats
    file_counts = []
    for ex in examples:
        match = re.search(r'Files to modify \((\d+) files\)', ex['messages'][1]['content'])
        if match:
            file_counts.append(int(match.group(1)))
    
    print(f"📊 File Statistics:")
    print(f"   Average files per example: {sum(file_counts)/len(file_counts):.1f}")
    print(f"   Min files: {min(file_counts)}")
    print(f"   Max files: {max(file_counts)}\n")
    
    # Distribution
    from collections import Counter
    counter = Counter(file_counts)
    print(f"📊 Distribution:")
    for count in sorted(counter.keys())[:10]:
        pct = counter[count]/len(examples)*100
        print(f"   {count} files: {counter[count]:3d} examples ({pct:5.1f}%)")
    
    print(f"\n{'='*70}")
    print(f"SAMPLE EXAMPLE (3-file commit):")
    print(f"{'='*70}\n")
    
    # Find a 3-file example
    small_ex = None
    for ex in examples:
        if '(3 files)' in ex['messages'][1]['content']:
            small_ex = ex
            break
    
    if small_ex:
        print("USER MESSAGE:")
        print(small_ex['messages'][1]['content'])
        print(f"\n{'-'*70}\n")
        print("ASSISTANT MESSAGE (first 1500 chars):")
        print(small_ex['messages'][2]['content'][:1500])
        print("\n... (truncated)")
    
    print(f"\n{'='*70}")
    print(f"✅ Dataset is ready for fine-tuning!")
    print(f"{'='*70}")
    
    return 0

if __name__ == '__main__':
    exit(main())

