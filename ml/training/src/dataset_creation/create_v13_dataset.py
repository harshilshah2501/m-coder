#!/usr/bin/env python3
"""
Create v13 dataset from v12 with proper format.

Fixes:
1. Add <thinking> wrapper with reasoning
2. Add <code> wrapper around diffs
3. Ensure File: prefix for all diffs
4. Ensure proper diff headers (--- a/ and +++ b/)
5. Remove metadata from messages
6. Filter out non-code examples (0 files)

Usage:
    python3 create_v13_dataset.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


def extract_file_path_from_diff(content: str) -> Optional[str]:
    """Extract file path from diff headers."""
    # Try --- a/path format
    match = re.search(r'---\s+a/([^\n]+)', content)
    if match:
        return match.group(1)
    
    # Try File: prefix
    match = re.search(r'File:\s*([^\n]+)', content)
    if match:
        return match.group(1).strip()
    
    return None


def has_code_changes(content: str) -> bool:
    """Check if content has actual code changes (hunks)."""
    return bool(re.search(r'@@\s+-\d+,\d+\s+\+\d+,\d+\s+@@', content))


def wrap_with_thinking(content: str, file_path: str, user_message: str) -> str:
    """
    Add <thinking> wrapper with basic reasoning.
    
    For v13, we'll add simple reasoning based on the task.
    In future iterations, we can use LLM to generate better reasoning.
    """
    # Extract task from user message
    task_match = re.search(r'Task:\s*([^\n]+)', user_message)
    task = task_match.group(1) if task_match else "Implement the requested changes"
    
    thinking = f"""<thinking>
I need to modify {file_path} to {task.lower()}.

Let me analyze the changes needed:
1. Locate the relevant code section
2. Apply the necessary modifications
3. Ensure the changes are minimal and focused

I'll generate a unified diff with proper format.
</thinking>"""
    
    return thinking


def format_as_proper_diff(content: str, file_path: str) -> str:
    """
    Ensure diff has proper format:
    - File: prefix
    - --- a/ and +++ b/ headers
    - Proper hunks
    """
    # Extract the actual diff content (remove existing wrappers)
    diff_content = content

    # Remove File: prefix if present
    if diff_content.strip().startswith('File:'):
        lines = diff_content.split('\n', 1)
        if len(lines) > 1:
            diff_content = lines[1]

    # Remove ```diff wrapper if present
    diff_content = re.sub(r'```diff\s*\n', '', diff_content)
    diff_content = re.sub(r'\n?```\s*$', '', diff_content)
    diff_content = diff_content.strip()

    # Check if diff has headers
    has_headers = bool(re.search(r'---\s+a/', diff_content))

    if not has_headers:
        # Add headers before the first hunk
        # Find first hunk
        hunk_match = re.search(r'(@@\s+-\d+,\d+\s+\+\d+,\d+\s+@@)', diff_content)
        if hunk_match:
            # Insert headers before first hunk
            before_hunk = diff_content[:hunk_match.start()]
            from_hunk = diff_content[hunk_match.start():]

            # Remove any index lines
            before_hunk = re.sub(r'index\s+[a-f0-9]+\.\.[a-f0-9]+\s+\d+\s*\n', '', before_hunk)

            diff_content = f"--- a/{file_path}\n+++ b/{file_path}\n{from_hunk}"

    # Wrap in proper format
    return f"File: {file_path}\n```diff\n{diff_content}\n```"


def transform_example(example: Dict) -> Optional[Dict]:
    """
    Transform a v12 example to v13 format.
    
    Returns None if example should be filtered out.
    """
    messages = example.get('messages', [])
    if len(messages) < 2:
        return None
    
    user_msg = None
    assistant_msg = None
    
    for msg in messages:
        if msg['role'] == 'user':
            user_msg = msg['content']
        elif msg['role'] == 'assistant':
            assistant_msg = msg['content']
    
    if not user_msg or not assistant_msg:
        return None
    
    # Filter out non-code examples
    if not has_code_changes(assistant_msg):
        return None
    
    # Extract file path
    file_path = extract_file_path_from_diff(assistant_msg)
    if not file_path:
        # Try to extract from user message
        match = re.search(r'File:\s*([^\n]+)', user_msg)
        if match:
            file_path = match.group(1).strip()
        else:
            return None  # Can't determine file path, skip
    
    # Strip motadata/ prefix if present
    if file_path.startswith('motadata/'):
        file_path = file_path[len('motadata/'):]
    
    # Add thinking wrapper
    thinking = wrap_with_thinking(assistant_msg, file_path, user_msg)
    
    # Format diff properly
    formatted_diff = format_as_proper_diff(assistant_msg, file_path)
    
    # Combine thinking + code
    new_assistant_msg = f"{thinking}\n\n<code>\n{formatted_diff}\n</code>"
    
    # Create new example (no metadata in messages)
    return {
        'messages': [
            {'role': 'system', 'content': messages[0]['content']} if messages[0]['role'] == 'system' else None,
            {'role': 'user', 'content': user_msg},
            {'role': 'assistant', 'content': new_assistant_msg}
        ]
    }


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    input_path = script_dir / "v12_combined.jsonl"
    output_path = script_dir / "v13_combined.jsonl"
    
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found")
        return 1
    
    print(f"📂 Reading {input_path}...")
    
    total = 0
    transformed = 0
    filtered = 0
    
    with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
        for line in f_in:
            if not line.strip():
                continue
            
            total += 1
            example = json.loads(line)
            
            new_example = transform_example(example)
            
            if new_example:
                # Remove None from messages (system message might be None)
                new_example['messages'] = [m for m in new_example['messages'] if m is not None]
                f_out.write(json.dumps(new_example) + '\n')
                transformed += 1
            else:
                filtered += 1
    
    print(f"\n✅ Transformation complete!")
    print(f"   Total examples: {total}")
    print(f"   Transformed: {transformed}")
    print(f"   Filtered out: {filtered}")
    print(f"   Output: {output_path}")
    
    return 0


if __name__ == '__main__':
    exit(main())

