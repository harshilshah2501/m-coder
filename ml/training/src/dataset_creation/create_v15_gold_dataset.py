#!/usr/bin/env python3
"""
Create V15 GOLD Dataset - 24-Carat Quality

UNIFIED FORMAT SPECIFICATION:
================================

1. NEW FILE CREATION (direct_generation, file_creation):
   Format: Plain code blocks (NO diffs, NO SEARCH-REPLACE)
   
   <thinking>
   [Analysis of what needs to be created]
   </thinking>
   
   <code>
   File: path/to/NewFile.java
   ```java
   [COMPLETE file content - no diff markers]
   ```
   </code>

2. EXISTING FILE EDITS (single_file, multi_file, refactoring):
   Format: SEARCH-REPLACE blocks (NO diffs, NO plain code)
   
   <thinking>
   [Analysis of what needs to be modified]
   </thinking>
   
   <code>
   File: path/to/ExistingFile.java
   <<<< SEARCH
   [exact code to find]
   ====
   [exact code to replace with]
   >>>> REPLACE
   </code>

3. OTHER (tool_use, code_review):
   Format: Keep as-is (no conversion needed)

NO INCONSISTENCIES:
- All examples MUST have <thinking> block
- All examples MUST have <code> block
- No mixing of formats within a category
- No diff headers (index, ---, +++)
- No @@ markers
- No +/- prefixes
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# CORRECTED CATEGORIZATION (after fixing inconsistencies):
# - code_edits: Edits from task description → SEARCH-REPLACE
# - single_file: Edits with context → SEARCH-REPLACE
# - multi_file: Multi-file edits → SEARCH-REPLACE
# - refactoring: Refactoring tasks → SEARCH-REPLACE
# - file_creation: New files → Plain code
# - diff_generation: Diff generation (was tool_use) → Keep as-is
# - code_review: Code review → Keep as-is

PLAIN_CODE_CATEGORIES = {'file_creation'}  # Only actual new files
SEARCH_REPLACE_CATEGORIES = {'code_edits', 'single_file', 'multi_file', 'refactoring'}
KEEP_AS_IS_CATEGORIES = {'diff_generation', 'code_review'}


def extract_plain_code_from_diff(diff_text: str, is_new_file: bool = False) -> str:
    """Extract complete file content from diff.

    For new files (/dev/null): extract all added lines
    For edits: extract added + context lines
    """
    lines = diff_text.split('\n')
    code_lines = []
    in_hunk = False

    for line in lines:
        # Skip diff metadata
        if line.startswith('index ') or line.startswith('---') or line.startswith('+++'):
            continue
        if line.startswith('@@'):
            in_hunk = True
            continue

        if in_hunk:
            if line.startswith('+') and not line.startswith('+++'):
                code_lines.append(line[1:])
            elif line.startswith(' ') and not is_new_file:
                # For edits, include context lines
                code_lines.append(line[1:])
            elif is_new_file and line.startswith(' '):
                # For new files, skip context (only added lines)
                pass

    return '\n'.join(code_lines)


def diff_to_search_replace(diff_text: str) -> str:
    """Convert unified diff to SEARCH-REPLACE format."""
    lines = diff_text.split('\n')
    blocks = []
    i = 0
    
    while i < len(lines):
        if lines[i].startswith('@@'):
            search_lines = []
            replace_lines = []
            i += 1
            
            while i < len(lines) and not lines[i].startswith('@@'):
                line = lines[i]
                if line.startswith('-') and not line.startswith('---'):
                    search_lines.append(line[1:])
                elif line.startswith('+') and not line.startswith('+++'):
                    replace_lines.append(line[1:])
                elif line.startswith(' '):
                    search_lines.append(line[1:])
                    replace_lines.append(line[1:])
                i += 1
            
            if search_lines or replace_lines:
                block = f"""<<<< SEARCH
{chr(10).join(search_lines)}
====
{chr(10).join(replace_lines)}
>>>> REPLACE"""
                blocks.append(block)
        else:
            i += 1
    
    return '\n\n'.join(blocks) if blocks else diff_text


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        '.java': 'java',
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.sh': 'bash',
        '.sql': 'sql',
    }
    
    for ext, lang in ext_map.items():
        if file_path.endswith(ext):
            return lang
    
    return 'java'  # Default


def convert_example(example: Dict) -> Dict:
    """Convert example to gold format."""
    category = example.get('metadata', {}).get('category')
    
    if not category or category in KEEP_AS_IS_CATEGORIES:
        return example
    
    messages = example.get('messages', [])
    if len(messages) < 2:
        return example
    
    assistant_msg = messages[-1]['content']
    
    # Extract thinking block
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', assistant_msg, re.DOTALL)
    thinking = thinking_match.group(1).strip() if thinking_match else ""
    
    # Extract code content (with or without <code> tags)
    code_match = re.search(r'<code>(.*?)</code>', assistant_msg, re.DOTALL)
    code_content = code_match.group(1).strip() if code_match else assistant_msg.strip()
    
    # Remove thinking from code_content if present
    code_content = re.sub(r'<thinking>.*?</thinking>', '', code_content, flags=re.DOTALL).strip()
    
    # Parse files from code content
    file_pattern = r'File: ([^\n]+)\n```(diff|java|python|javascript|typescript|json|xml|yaml|bash|sql)?\n(.*?)```'
    file_matches = list(re.finditer(file_pattern, code_content, re.DOTALL))

    # If no File: prefix found, try to extract file path from diff headers
    if not file_matches and '---' in code_content and '+++' in code_content:
        # Extract file path from diff headers
        diff_file_pattern = r'\+\+\+ b/([^\n]+)'
        diff_match = re.search(diff_file_pattern, code_content)
        if diff_match:
            file_path = diff_match.group(1)
            # Wrap the entire diff content
            file_matches = [type('Match', (), {
                'group': lambda self, n: {
                    1: file_path,
                    2: 'diff',
                    3: code_content
                }.get(n)
            })()]

    if not file_matches:
        return example
    
    converted_files = []
    
    for match in file_matches:
        file_path = match.group(1).strip()
        lang = match.group(2) or 'diff'
        file_content = match.group(3).strip()
        
        if category in PLAIN_CODE_CATEGORIES:
            # Convert to plain code
            if lang == 'diff':
                # Check if this is a new file (has /dev/null)
                is_new_file = '/dev/null' in file_content
                plain_code = extract_plain_code_from_diff(file_content, is_new_file=is_new_file)
                detected_lang = detect_language(file_path)
                converted_files.append(f"File: {file_path}\n```{detected_lang}\n{plain_code}\n```")
            else:
                converted_files.append(f"File: {file_path}\n```{lang}\n{file_content}\n```")
        
        elif category in SEARCH_REPLACE_CATEGORIES:
            # Convert to SEARCH-REPLACE
            if lang == 'diff':
                search_replace = diff_to_search_replace(file_content)
                converted_files.append(f"File: {file_path}\n{search_replace}")
            else:
                converted_files.append(f"File: {file_path}\n```{lang}\n{file_content}\n```")
    
    # Reconstruct with proper format
    new_code_block = '\n\n'.join(converted_files)
    new_assistant_msg = f"<thinking>\n{thinking}\n</thinking>\n\n<code>\n{new_code_block}\n</code>"
    
    messages[-1]['content'] = new_assistant_msg
    example['messages'] = messages

    return example


def main():
    """Main conversion process."""
    workspace_root = Path('/home/harshil/Harshil-PoCs')
    input_file = workspace_root / 'datasets' / 'v15_corrected.jsonl'
    output_file = workspace_root / 'datasets' / 'v15_gold.jsonl'

    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"\nCreating 24-CARAT GOLD dataset...")
    print("=" * 70)

    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        return

    converted_count = 0
    category_stats = {}
    error_count = 0

    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line_num, line in enumerate(f_in, 1):
            try:
                example = json.loads(line)
                converted = convert_example(example)

                category = converted.get('metadata', {}).get('category', 'unknown')
                category_stats[category] = category_stats.get(category, 0) + 1

                f_out.write(json.dumps(converted) + '\n')
                converted_count += 1

                if converted_count % 500 == 0:
                    print(f"✓ Processed {converted_count} examples...")

            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"⚠ ERROR on line {line_num}: {str(e)[:100]}")
                continue

    print("\n" + "=" * 70)
    print(f"✅ GOLD Dataset Creation Complete!")
    print(f"\nStatistics:")
    print(f"  Total examples: {converted_count}")
    print(f"  Errors: {error_count}")
    print(f"\nCategory Distribution:")
    for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        pct = (count / converted_count * 100) if converted_count > 0 else 0
        print(f"  {cat:20s}: {count:4d} ({pct:5.1f}%)")

    print(f"\nOutput file: {output_file}")
    print(f"File size: {output_file.stat().st_size / (1024*1024):.1f} MB")


if __name__ == '__main__':
    main()

