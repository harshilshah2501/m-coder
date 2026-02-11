#!/usr/bin/env python3
"""
Create V15 Hybrid SEARCH-REPLACE Dataset

Strategy:
1. NEW FILES (direct_generation, file_creation) → Plain code blocks
2. EXISTING FILE EDITS (single_file, multi_file, refactoring) → SEARCH-REPLACE format
3. OTHER (tool_use, code_review) → Keep as-is

Input: v15_balanced_unified_diff_20251229.jsonl (unified diff format)
Output: v15_hybrid_search_replace.jsonl (hybrid format)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Categories that should use PLAIN CODE (new files)
PLAIN_CODE_CATEGORIES = {'direct_generation', 'file_creation'}

# Categories that should use SEARCH-REPLACE (existing file edits)
SEARCH_REPLACE_CATEGORIES = {'single_file', 'multi_file', 'refactoring'}

# Categories to keep as-is
KEEP_AS_IS_CATEGORIES = {'tool_use', 'code_review'}


def extract_diff_hunks(diff_text: str) -> List[Dict]:
    """Extract hunks from unified diff format."""
    hunks = []
    lines = diff_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Find hunk header: @@ -10,7 +10,8 @@
        if line.startswith('@@'):
            hunk = {'header': line, 'removed': [], 'added': [], 'context': []}
            i += 1
            
            # Collect hunk lines
            while i < len(lines) and not lines[i].startswith('@@'):
                if lines[i].startswith('-'):
                    hunk['removed'].append(lines[i][1:])  # Remove '-' prefix
                elif lines[i].startswith('+'):
                    hunk['added'].append(lines[i][1:])  # Remove '+' prefix
                elif lines[i].startswith(' '):
                    hunk['context'].append(lines[i][1:])  # Remove ' ' prefix
                i += 1
            
            hunks.append(hunk)
        else:
            i += 1
    
    return hunks


def diff_to_search_replace(diff_text: str, file_path: str) -> str:
    """Convert unified diff to SEARCH-REPLACE format."""
    lines = diff_text.split('\n')
    search_replace_blocks = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Find hunk header: @@ -10,7 +10,8 @@
        if line.startswith('@@'):
            search_lines = []
            replace_lines = []
            i += 1

            # Collect lines until next hunk or end
            while i < len(lines) and not lines[i].startswith('@@'):
                current = lines[i]

                if current.startswith('-') and not current.startswith('---'):
                    # Line to be removed (goes in SEARCH)
                    search_lines.append(current[1:])
                elif current.startswith('+') and not current.startswith('+++'):
                    # Line to be added (goes in REPLACE)
                    replace_lines.append(current[1:])
                elif current.startswith(' '):
                    # Context line (goes in both)
                    search_lines.append(current[1:])
                    replace_lines.append(current[1:])

                i += 1

            # Create SEARCH-REPLACE block
            if search_lines or replace_lines:
                block = f"""<<<< SEARCH
{chr(10).join(search_lines)}
====
{chr(10).join(replace_lines)}
>>>> REPLACE"""
                search_replace_blocks.append(block)
        else:
            i += 1

    return '\n\n'.join(search_replace_blocks) if search_replace_blocks else diff_text


def diff_to_plain_code(diff_text: str) -> str:
    """Extract plain code from unified diff (for new files)."""
    lines = diff_text.split('\n')
    code_lines = []

    in_hunk = False
    for line in lines:
        # Skip diff headers
        if line.startswith('index ') or line.startswith('---') or line.startswith('+++'):
            continue

        # Start of hunk
        if line.startswith('@@'):
            in_hunk = True
            continue

        # Extract added lines (new content)
        if in_hunk:
            if line.startswith('+'):
                code_lines.append(line[1:])  # Remove '+' prefix
            elif line.startswith(' '):
                code_lines.append(line[1:])  # Context lines (for edits to existing files)

    return '\n'.join(code_lines)


def convert_example(example: Dict) -> Dict:
    """Convert a single example to hybrid format."""
    category = example.get('metadata', {}).get('category')

    if not category:
        return example  # Keep unchanged if no category

    # Keep as-is categories
    if category in KEEP_AS_IS_CATEGORIES:
        return example

    # Get assistant message
    messages = example.get('messages', [])
    if len(messages) < 2:
        return example

    assistant_msg = messages[-1]['content']

    # Try to extract code blocks from <code>...</code>
    code_pattern = r'<code>(.*?)</code>'
    code_match = re.search(code_pattern, assistant_msg, re.DOTALL)

    if code_match:
        code_content = code_match.group(1)
        has_code_tags = True
    else:
        # For direct_generation, the content might be plain diffs without <code> tags
        code_content = assistant_msg
        has_code_tags = False

    # Process each file in the code block
    file_pattern = r'File: ([^\n]+)\n```(diff|java|python|javascript|json)?\n(.*?)```'
    file_matches = list(re.finditer(file_pattern, code_content, re.DOTALL))

    if not file_matches:
        # Debug: pattern didn't match
        return example

    converted_files = []
    for match in file_matches:
        file_path = match.group(1).strip()
        lang = match.group(2) or 'diff'
        file_content = match.group(3).strip()

        # Convert based on category
        if category in PLAIN_CODE_CATEGORIES:
            # Convert diff to plain code
            if lang == 'diff':
                plain_code = diff_to_plain_code(file_content)
                # Detect language from file extension
                if file_path.endswith('.java'):
                    detected_lang = 'java'
                elif file_path.endswith('.py'):
                    detected_lang = 'python'
                elif file_path.endswith('.js'):
                    detected_lang = 'javascript'
                elif file_path.endswith('.json'):
                    detected_lang = 'json'
                else:
                    detected_lang = 'java'  # Default

                converted_files.append(f"File: {file_path}\n```{detected_lang}\n{plain_code}\n```")
            else:
                # Already plain code
                converted_files.append(f"File: {file_path}\n```{lang}\n{file_content}\n```")

        elif category in SEARCH_REPLACE_CATEGORIES:
            # Convert diff to SEARCH-REPLACE
            if lang == 'diff':
                search_replace = diff_to_search_replace(file_content, file_path)
                converted_files.append(f"File: {file_path}\n{search_replace}")
            else:
                # Already in some format, keep as-is
                converted_files.append(f"File: {file_path}\n```{lang}\n{file_content}\n```")

    # Reconstruct assistant message
    if has_code_tags:
        # Extract thinking block if present
        thinking_pattern = r'(<thinking>.*?</thinking>)'
        thinking_match = re.search(thinking_pattern, assistant_msg, re.DOTALL)
        thinking = thinking_match.group(1) if thinking_match else ""

        new_code_block = '\n\n'.join(converted_files)
        new_assistant_msg = f"{thinking}\n\n<code>\n{new_code_block}\n</code>"
    else:
        # For plain diffs without code tags, just join the converted files
        new_assistant_msg = '\n\n'.join(converted_files)

    # Update message
    messages[-1]['content'] = new_assistant_msg
    example['messages'] = messages

    return example


def main():
    """Main conversion process."""
    # Use absolute paths from workspace root
    workspace_root = Path('/home/harshil/Harshil-PoCs')
    input_file = workspace_root / 'datasets' / 'archive' / 'v15_balanced_unified_diff_20251229.jsonl'
    output_file = workspace_root / 'datasets' / 'v15_hybrid_search_replace.jsonl'

    print(f"Input: {input_file}")
    print(f"Output: {output_file}")

    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        return

    # Process examples
    converted_count = 0
    category_stats = {}

    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line_num, line in enumerate(f_in, 1):
            try:
                example = json.loads(line)
                converted = convert_example(example)

                # Track stats
                category = converted.get('metadata', {}).get('category', 'unknown')
                category_stats[category] = category_stats.get(category, 0) + 1

                f_out.write(json.dumps(converted) + '\n')
                converted_count += 1

                if converted_count % 100 == 0:
                    print(f"Processed {converted_count} examples...")

            except Exception as e:
                print(f"ERROR on line {line_num}: {e}")
                continue

    print(f"\n✅ Conversion complete!")
    print(f"Total examples: {converted_count}")
    print(f"\nCategory distribution:")
    for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()

