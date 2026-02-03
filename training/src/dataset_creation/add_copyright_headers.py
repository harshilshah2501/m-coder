#!/usr/bin/env python3
"""
Add Motadata copyright headers to file_creation examples

This script adds copyright headers to all file_creation examples that don't have them.
"""

import json
from pathlib import Path
from typing import Dict
import re


MOTADATA_COPYRIGHT = """/*
 * Copyright (c) 2024 Mindarray Systems Pvt. Ltd.
 * All rights reserved.
 */
"""


def extract_file_path(content: str) -> str:
    """Extract file path from content."""
    match = re.search(r'File:\s*([^\n]+)', content)
    if match:
        return match.group(1).strip()
    return None


def get_copyright_for_language(file_path: str) -> str:
    """Get appropriate copyright header for file type."""
    if file_path.endswith('.java'):
        return MOTADATA_COPYRIGHT
    elif file_path.endswith('.py'):
        return """# Copyright (c) 2024 Mindarray Systems Pvt. Ltd.
# All rights reserved.
"""
    elif file_path.endswith('.js') or file_path.endswith('.ts'):
        return """/*
 * Copyright (c) 2024 Mindarray Systems Pvt. Ltd.
 * All rights reserved.
 */
"""
    elif file_path.endswith('.go'):
        return """// Copyright (c) 2024 Mindarray Systems Pvt. Ltd.
// All rights reserved.
"""
    else:
        return MOTADATA_COPYRIGHT


def has_copyright(content: str) -> bool:
    """Check if content already has copyright header."""
    return 'copyright' in content.lower() or 'mindarray' in content.lower()


def add_copyright_to_code_block(code_block: str, file_path: str) -> str:
    """Add copyright header to code block."""
    if has_copyright(code_block):
        return code_block
    
    copyright_header = get_copyright_for_language(file_path)
    
    # Extract the code content (after File: line)
    lines = code_block.split('\n')
    file_line_idx = -1
    
    for i, line in enumerate(lines):
        if line.startswith('File:'):
            file_line_idx = i
            break
    
    if file_line_idx == -1:
        return code_block
    
    # Reconstruct with copyright
    result = '\n'.join(lines[:file_line_idx + 1]) + '\n'
    result += copyright_header + '\n'
    result += '\n'.join(lines[file_line_idx + 1:])
    
    return result


def process_dataset(input_file: Path, output_file: Path) -> Dict:
    """Process dataset and add copyright headers."""
    stats = {
        'total': 0,
        'file_creation': 0,
        'with_copyright': 0,
        'headers_added': 0,
        'errors': 0
    }
    
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line_num, line in enumerate(f_in, 1):
            try:
                example = json.loads(line)
                stats['total'] += 1
                
                category = example.get('metadata', {}).get('category')
                
                if category == 'file_creation':
                    stats['file_creation'] += 1
                    content = example['messages'][-1]['content']
                    
                    if has_copyright(content):
                        stats['with_copyright'] += 1
                    else:
                        # Add copyright header
                        file_path = extract_file_path(content)
                        if file_path:
                            new_content = add_copyright_to_code_block(content, file_path)
                            example['messages'][-1]['content'] = new_content
                            stats['headers_added'] += 1
                
                f_out.write(json.dumps(example) + '\n')
                
                if stats['total'] % 500 == 0:
                    print(f"✓ Processed {stats['total']} examples...")
            
            except Exception as e:
                stats['errors'] += 1
                print(f"⚠ ERROR on line {line_num}: {str(e)[:100]}")
                continue
    
    return stats


def main():
    workspace_root = Path('/home/harshil/Harshil-PoCs')
    input_file = workspace_root / 'datasets' / 'v15_final.jsonl'
    output_file = workspace_root / 'datasets' / 'v15_with_copyright.jsonl'
    
    print("="*80)
    print("Adding Copyright Headers to file_creation Examples")
    print("="*80)
    print(f"\nInput:  {input_file}")
    print(f"Output: {output_file}")
    print()
    
    stats = process_dataset(input_file, output_file)
    
    print("\n" + "="*80)
    print("✅ Copyright Header Addition Complete!")
    print("="*80)
    print(f"\nStatistics:")
    print(f"  Total examples: {stats['total']}")
    print(f"  file_creation examples: {stats['file_creation']}")
    print(f"  Already with copyright: {stats['with_copyright']}")
    print(f"  Headers added: {stats['headers_added']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\nOutput file: {output_file}")
    print(f"File size: {output_file.stat().st_size / (1024*1024):.1f} MB")
    print()


if __name__ == '__main__':
    main()

