#!/usr/bin/env python3
"""
Convert V14 Git Diff Training Data to V15 Search/Replace Format

This script transforms unified diff format into Search/Replace blocks
that are more robust for LLM code generation.

Input Format (V14):
```diff
@@ -10,5 +10,4 @@
 context line
-removed line
+added line
 context line
```

Output Format (V15):
<<<< SEARCH
context line
removed line
context line
====
context line
added line
context line
>>>> REPLACE

Benefits:
- No line numbers (survives code shifts)
- Fuzzy matching possible
- Self-verifying (if SEARCH not found, you know it failed)
- Industry standard (Aider, Cursor, Cline use this)

Usage:
    python3 convert_diff_to_search_replace.py --input v14_multifile_final.jsonl --output v15_search_replace.jsonl
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Tuple, Optional


def parse_unified_diff_hunk(hunk_lines: List[str]) -> Tuple[List[str], List[str]]:
    """
    Parse a unified diff hunk into SEARCH and REPLACE content.
    
    Args:
        hunk_lines: Lines of the hunk (starting after @@ header)
    
    Returns:
        (search_lines, replace_lines)
    """
    search_lines = []
    replace_lines = []
    
    for line in hunk_lines:
        if not line:  # Empty line
            search_lines.append('')
            replace_lines.append('')
        elif line.startswith(' '):  # Context line
            search_lines.append(line[1:])
            replace_lines.append(line[1:])
        elif line.startswith('-'):  # Removed line
            search_lines.append(line[1:])
        elif line.startswith('+'):  # Added line
            replace_lines.append(line[1:])
        elif line.startswith('\\'):  # "\ No newline at end of file"
            continue
        else:
            # Unknown line type - treat as context
            search_lines.append(line)
            replace_lines.append(line)
    
    return search_lines, replace_lines


def convert_diff_to_search_replace(diff_content: str) -> str:
    """
    Convert a unified diff to Search/Replace format.
    
    Args:
        diff_content: The unified diff content
    
    Returns:
        Search/Replace formatted content
    """
    result_blocks = []
    
    # Split by hunk headers
    hunk_pattern = r'@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@.*?\n'
    
    # Find all hunks
    hunks = re.split(hunk_pattern, diff_content)
    hunk_headers = re.findall(hunk_pattern, diff_content)
    
    # Skip the first split (before first hunk) if it's just headers
    if hunks and hunks[0].strip():
        # First part might contain --- and +++ headers, skip it
        if hunks[0].strip().startswith('---') or hunks[0].strip().startswith('index'):
            hunks = hunks[1:]
        else:
            hunks = hunks[1:]
    else:
        hunks = hunks[1:]
    
    for i, hunk in enumerate(hunks):
        if not hunk.strip():
            continue
        
        lines = hunk.split('\n')
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()
        
        if not lines:
            continue
        
        search_lines, replace_lines = parse_unified_diff_hunk(lines)
        
        # Skip if nothing changed
        if search_lines == replace_lines:
            continue
        
        # Build Search/Replace block
        search_content = '\n'.join(search_lines)
        replace_content = '\n'.join(replace_lines)
        
        block = f"""<<<< SEARCH
{search_content}
====
{replace_content}
>>>> REPLACE"""
        
        result_blocks.append(block)
    
    return '\n\n'.join(result_blocks)


def convert_assistant_content(content: str) -> str:
    """
    Convert assistant content from diff format to Search/Replace format.
    
    Preserves <thinking> and <code> blocks, converts diffs inside.
    """
    # Find <code> block
    code_match = re.search(r'<code>(.*?)</code>', content, re.DOTALL)
    if not code_match:
        return content
    
    code_block = code_match.group(1)
    
    # Split by File: prefix
    file_pattern = r'File:\s*([^\n]+)\n```diff\n(.*?)```'
    matches = re.findall(file_pattern, code_block, re.DOTALL)
    
    if not matches:
        return content
    
    # Convert each file's diff
    new_code_parts = []
    for file_path, diff_content in matches:
        file_path = file_path.strip()
        search_replace = convert_diff_to_search_replace(diff_content)
        
        if search_replace.strip():
            new_code_parts.append(f"File: {file_path}\n{search_replace}")
    
    new_code_block = '\n\n'.join(new_code_parts)

    # Replace old code block with new
    new_content = content[:code_match.start()] + f"<code>\n{new_code_block}\n</code>" + content[code_match.end():]

    return new_content


# V15 System Prompt - Updated for Search/Replace format
V15_SYSTEM_PROMPT = """You are a senior Motadata engineer. Given a task and multiple files to modify, generate precise Search/Replace blocks for each file.

CRITICAL REQUIREMENTS:
- Generate Search/Replace blocks for ALL files listed in the task
- Use this exact format for each change:

File: path/to/file.java
<<<< SEARCH
[exact code to find - include enough context for unique match]
====
[replacement code]
>>>> REPLACE

- The SEARCH block must contain EXACTLY the code that exists in the file
- Include 2-3 lines of context before/after the change for reliable matching
- Do NOT include line numbers
- Multiple changes to the same file should have multiple SEARCH/REPLACE blocks
- Ensure changes are consistent across all files"""


def convert_system_prompt(content: str) -> str:
    """Update system prompt to V15 format."""
    # Check if it's a V14-style prompt about diffs
    if 'unified diff' in content.lower() or 'diff format' in content.lower():
        return V15_SYSTEM_PROMPT
    return content


def convert_example(example: dict) -> dict:
    """Convert a single training example from V14 to V15 format."""
    messages = example.get('messages', [])
    new_messages = []

    for msg in messages:
        new_msg = msg.copy()

        if msg['role'] == 'system':
            new_msg['content'] = convert_system_prompt(msg['content'])
        elif msg['role'] == 'assistant':
            new_msg['content'] = convert_assistant_content(msg['content'])

        new_messages.append(new_msg)

    return {'messages': new_messages}


def main():
    parser = argparse.ArgumentParser(
        description='Convert V14 diff format to V15 Search/Replace format'
    )
    parser.add_argument(
        '--input', '-i',
        default='v14_multifile_final.jsonl',
        help='Input JSONL file (V14 format)'
    )
    parser.add_argument(
        '--output', '-o',
        default='v15_search_replace.jsonl',
        help='Output JSONL file (V15 format)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed conversion info'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    input_path = script_dir / args.input
    output_path = script_dir / args.output

    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return 1

    print(f"Converting V14 → V15 format")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print("=" * 60)

    converted = 0
    errors = 0

    with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
        for line_num, line in enumerate(f_in, 1):
            if not line.strip():
                continue

            try:
                example = json.loads(line)
                converted_example = convert_example(example)
                f_out.write(json.dumps(converted_example) + '\n')
                converted += 1

                if args.verbose and converted <= 3:
                    print(f"\n--- Example {converted} ---")
                    print(converted_example['messages'][-1]['content'][:500] + "...")

            except Exception as e:
                errors += 1
                print(f"⚠️ Error on line {line_num}: {e}")

    print("=" * 60)
    print(f"✅ Converted: {converted} examples")
    if errors:
        print(f"⚠️ Errors: {errors}")
    print(f"📁 Output: {output_path}")

    return 0


if __name__ == '__main__':
    exit(main())

