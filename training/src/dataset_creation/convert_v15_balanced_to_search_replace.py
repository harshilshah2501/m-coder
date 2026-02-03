#!/usr/bin/env python3
"""
Convert v15_balanced.jsonl (2,599 examples) to Search/Replace format.

This preserves ALL capabilities from V12/V13/V14:
- Tool use patterns
- Single-file edits
- Multi-file commits
- Direct generation
- Code review
- Reasoning/thinking

While adding the new Search/Replace format for better parsing.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

# Input/Output
INPUT_FILE = Path("v15_balanced.jsonl")
OUTPUT_FILE = Path("v15_balanced_search_replace.jsonl")
SURVEY_FILE = Path("v15_balanced_survey_report.json")

# V15 System Prompt for Search/Replace format
SEARCH_REPLACE_SYSTEM_PROMPT = """You are a senior Motadata engineer. Given a task and files to modify, generate precise Search/Replace blocks.

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
- DO NOT include line numbers
- Multiple changes to the same file should have multiple SEARCH/REPLACE blocks
- Ensure changes are consistent across all files"""


def extract_diff_hunks(diff_text: str) -> List[Dict]:
    """Extract individual file changes from unified diff."""
    hunks = []
    current_file = None
    current_hunk = []

    # Remove markdown code fence if present
    diff_text = re.sub(r'^```diff\s*\n', '', diff_text, flags=re.MULTILINE)
    diff_text = re.sub(r'\n```\s*$', '', diff_text)

    # Also handle "File: path" prefix lines
    lines = diff_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for "File: path" prefix
        if line.startswith('File: '):
            # Extract file path from "File: path" line
            file_match = re.match(r'File:\s*(.+)', line)
            if file_match:
                if current_file and current_hunk:
                    hunks.append({
                        'file': current_file,
                        'lines': current_hunk
                    })
                    current_hunk = []
                current_file = file_match.group(1)
            i += 1
            continue

        # File marker from diff
        if line.startswith('diff --git') or line.startswith('+++'):
            if current_file and current_hunk:
                hunks.append({
                    'file': current_file,
                    'lines': current_hunk
                })
                current_hunk = []

            if line.startswith('+++'):
                # Extract filename from +++ b/path/to/file
                match = re.search(r'\+\+\+ b/(.+)', line)
                if match:
                    current_file = match.group(1)

        # Hunk content
        elif line.startswith('@@') or line.startswith('+') or line.startswith('-') or line.startswith(' '):
            current_hunk.append(line)

        i += 1

    # Add last hunk
    if current_file and current_hunk:
        hunks.append({
            'file': current_file,
            'lines': current_hunk
        })

    return hunks


def diff_to_search_replace(hunk: Dict) -> Optional[str]:
    """Convert a diff hunk to Search/Replace format."""
    lines = hunk['lines']
    file_path = hunk['file']

    search_lines = []
    replace_lines = []
    context_before = []
    context_after = []

    in_change = False
    has_deletions = False

    for line in lines:
        if line.startswith('@@'):
            continue

        if line.startswith('-'):
            # Removed line
            search_lines.append(line[1:])  # Remove '-' prefix
            in_change = True
            has_deletions = True
        elif line.startswith('+'):
            # Added line
            replace_lines.append(line[1:])  # Remove '+' prefix
            in_change = True
        elif line.startswith(' '):
            # Context line
            context_line = line[1:]  # Remove ' ' prefix

            if not in_change:
                # Before the change
                context_before.append(context_line)
                if len(context_before) > 3:
                    context_before.pop(0)  # Keep only last 3 lines
            else:
                # After the change
                context_after.append(context_line)
                if len(context_after) >= 3:
                    break  # We have enough context

    # If there are no deletions (new file or pure additions), return None
    # These should be kept in original diff format
    if not has_deletions:
        return None

    # Build SEARCH block (context + removed lines + context)
    search_block = context_before + search_lines + context_after

    # Build REPLACE block (context + added lines + context)
    replace_block = context_before + replace_lines + context_after

    if not search_block or not replace_block:
        return None

    # Format as Search/Replace
    result = f"File: {file_path}\n"
    result += "<<<< SEARCH\n"
    result += "\n".join(search_block) + "\n"
    result += "====\n"
    result += "\n".join(replace_block) + "\n"
    result += ">>>> REPLACE\n"

    return result


def convert_example(example: Dict) -> Optional[Dict]:
    """Convert a single example from diff format to Search/Replace format."""
    messages = example.get('messages', [])

    if not messages:
        return None

    # Find assistant message
    assistant_msg = None
    for msg in messages:
        if msg['role'] == 'assistant':
            assistant_msg = msg
            break

    if not assistant_msg:
        return None

    content = assistant_msg.get('content', '')

    # If no <code> tag, preserve as-is (code review, tool use, etc.)
    if '<code>' not in content:
        return example
    
    content = assistant_msg['content']
    
    # Extract thinking block
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
    thinking = thinking_match.group(1).strip() if thinking_match else ""
    
    # Extract code block
    code_match = re.search(r'<code>(.*?)</code>', content, re.DOTALL)
    if not code_match:
        return None
    
    code_content = code_match.group(1).strip()

    # Extract diff blocks
    hunks = extract_diff_hunks(code_content)

    if not hunks:
        # No hunks found, keep original
        return example

    # Convert each hunk to Search/Replace
    search_replace_blocks = []
    for hunk in hunks:
        sr_block = diff_to_search_replace(hunk)
        if sr_block:
            search_replace_blocks.append(sr_block)

    if not search_replace_blocks:
        # No hunks could be converted (e.g., new files with only additions)
        # Keep original format
        return example

    # Build new assistant message
    new_content = ""
    if thinking:
        new_content += f"<thinking>\n{thinking}\n</thinking>\n\n"

    new_content += "<code>\n"
    new_content += "\n".join(search_replace_blocks)
    new_content += "</code>"

    # Create new example with updated assistant message
    new_messages = []
    for msg in messages:
        if msg['role'] == 'assistant' and msg == assistant_msg:
            new_messages.append({
                'role': 'assistant',
                'content': new_content
            })
        else:
            new_messages.append(msg)

    # Update system prompt if present
    for msg in new_messages:
        if msg['role'] == 'system':
            msg['content'] = SEARCH_REPLACE_SYSTEM_PROMPT
            break
    else:
        # Add system prompt if not present
        new_messages.insert(0, {
            'role': 'system',
            'content': SEARCH_REPLACE_SYSTEM_PROMPT
        })

    return {'messages': new_messages}


def main():
    print("=" * 80)
    print("Converting v15_balanced.jsonl to Search/Replace Format")
    print("=" * 80)
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Survey: {SURVEY_FILE}")
    print()

    if not INPUT_FILE.exists():
        print(f"❌ Error: {INPUT_FILE} not found!")
        return 1

    # Load survey data
    survey_data = None
    convert_indices = set()
    if SURVEY_FILE.exists():
        print("Loading survey data...")
        with open(SURVEY_FILE, 'r') as f:
            survey_data = json.load(f)

        # Get indices of examples that need conversion (single_file_diff and multi_file_diff)
        all_analyses = survey_data.get('all_analyses', [])
        for analysis in all_analyses:
            if analysis['pattern'] in ['single_file_diff', 'multi_file_diff']:
                convert_indices.add(analysis['index'])

        print(f"✅ Survey loaded: {len(convert_indices)} examples need conversion")
        print(f"   Patterns to convert: single_file_diff, multi_file_diff")
    else:
        print("⚠️  Survey file not found, will attempt to convert all examples")

    # Load examples
    print("\nLoading examples...")
    examples = []
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    print(f"✅ Loaded {len(examples)} examples")

    # Convert examples
    print("\nConverting to Search/Replace format...")
    converted = []
    skipped = []
    failed = []

    for i, example in enumerate(examples):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i + 1}/{len(examples)}")

        # If we have survey data, only convert specific patterns
        if survey_data and i not in convert_indices:
            # Keep as-is for other patterns
            converted.append(example)
            skipped.append(i)
            continue

        result = convert_example(example)
        if result:
            converted.append(result)
        else:
            failed.append(i)

    print(f"\n✅ Converted: {len(converted)} total examples")
    if survey_data:
        print(f"   - Transformed to Search/Replace: {len(convert_indices) - len(failed)}")
        print(f"   - Kept as-is: {len(skipped)}")
    print(f"⚠️  Failed: {len(failed)} examples")

    if failed:
        print(f"   Failed indices: {failed[:10]}{'...' if len(failed) > 10 else ''}")

    # Save converted examples
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        for example in converted:
            f.write(json.dumps(example) + '\n')

    print(f"✅ Saved {len(converted)} examples")

    # Show sample
    if converted:
        print("\n" + "=" * 80)
        print("Sample Converted Example (first 1000 chars):")
        print("=" * 80)
        sample = converted[0]['messages'][-1]['content']
        print(sample[:1000])
        print("...")

    print("\n" + "=" * 80)
    print("✅ CONVERSION COMPLETE!")
    print("=" * 80)
    print(f"Output: {OUTPUT_FILE}")
    print(f"Examples: {len(converted)}")
    print("\nNext steps:")
    print("  1. Validate: python3 validate_v15_balanced_search_replace.py")
    print("  2. Train: python3 train_v15_balanced_search_replace.py")

    return 0


if __name__ == '__main__':
    exit(main())

