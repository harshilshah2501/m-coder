#!/usr/bin/env python3
"""
Create v14 dataset with multi-file examples.

Key improvements over v13:
1. Keep multi-file commits together (don't split into single files)
2. Filter out Patch*.java files
3. Prioritize commits with 3+ files
4. Add proper <thinking> and <code> wrappers
5. Ensure proper diff format for each file

Usage:
    python3 create_v14_multifile_dataset.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict


def should_include_file(file_path: str) -> bool:
    """Check if file should be included (filter out Patch*.java)."""
    # Exclude Patch files
    if re.search(r'/Patch\d+\.java$', file_path):
        return False
    
    # Only include .java files
    if not file_path.endswith('.java'):
        return False
    
    return True


def extract_file_changes(file_data: dict) -> Optional[dict]:
    """Extract file path and diff from file data."""
    path = file_data.get('path', '')
    diff = file_data.get('diff', '')
    
    if not path or not diff:
        return None
    
    # Check if diff has actual changes (hunks)
    if not re.search(r'@@\s+-\d+,\d+\s+\+\d+,\d+\s+@@', diff):
        return None
    
    return {
        'path': path,
        'diff': diff
    }


def format_multifile_diff(files: List[dict]) -> str:
    """Format multiple files into proper diff format."""
    formatted_files = []
    
    for file_info in files:
        path = file_info['path']
        diff = file_info['diff']
        
        # Strip motadata/ prefix if present
        if path.startswith('motadata/'):
            path = path[len('motadata/'):]
        
        # Ensure diff has proper headers
        if not re.search(r'---\s+a/', diff):
            # Add headers if missing
            diff = f"--- a/{path}\n+++ b/{path}\n{diff}"
        
        # Format with File: prefix
        formatted = f"File: {path}\n```diff\n{diff.strip()}\n```"
        formatted_files.append(formatted)
    
    return '\n\n'.join(formatted_files)


def create_thinking_block(commit_msg: str, files: List[dict]) -> str:
    """Create <thinking> block for multi-file changes."""
    file_count = len(files)
    file_list = ', '.join([f['path'].split('/')[-1] for f in files[:3]])
    if file_count > 3:
        file_list += f', and {file_count - 3} more'
    
    thinking = f"""<thinking>
**Task**: {commit_msg}

**Files to modify** ({file_count} files):
{chr(10).join([f'- {f["path"]}' for f in files])}

**Plan**:
1. Analyze the required changes across all files
2. Ensure consistency across the codebase
3. Apply changes in proper order
4. Maintain code quality and patterns

**Approach**: Generate unified diffs for each file with proper format.
</thinking>"""
    
    return thinking


def transform_commit_to_example(commit_id: str, task_desc: str, files_data: List[dict]) -> Optional[dict]:
    """
    Transform a commit with multiple files into a training example.

    Returns None if commit should be filtered out.
    """
    if not commit_id or not task_desc or not files_data:
        return None

    # Extract and filter files
    valid_files = []
    for file_data in files_data:
        path = file_data.get('path', '')

        if not should_include_file(path):
            continue

        # Get diff from expected_diff field
        diff = file_data.get('expected_diff', '')
        if not diff or not re.search(r'@@\s+-\d+,\d+\s+\+\d+,\d+\s+@@', diff):
            continue

        valid_files.append({
            'path': path,
            'diff': diff
        })
    
    # Skip if no valid files or only 1-2 files (prioritize multi-file)
    if len(valid_files) < 3:
        return None

    # Create thinking block
    thinking = create_thinking_block(task_desc, valid_files)
    
    # Format all diffs
    formatted_diffs = format_multifile_diff(valid_files)
    
    # Combine thinking + code
    assistant_msg = f"{thinking}\n\n<code>\n{formatted_diffs}\n</code>"
    
    # Create user message with file list
    file_list = '\n'.join([f"{i+1}. {f['path']}" for i, f in enumerate(valid_files)])
    user_msg = f"""Task: {task_desc}

Files to modify ({len(valid_files)} files):
{file_list}

Generate unified diffs for all files to implement this change."""
    
    # System message
    system_msg = """You are a senior Motadata engineer. Given a task and multiple files to modify, generate precise unified diffs for each file.

CRITICAL REQUIREMENTS:
- Generate diffs for ALL files listed in the task
- Use proper unified diff format with --- a/ and +++ b/ headers
- Include File: prefix for each file
- Wrap each diff in ```diff blocks
- Ensure changes are consistent across all files"""
    
    return {
        'messages': [
            {'role': 'system', 'content': system_msg},
            {'role': 'user', 'content': user_msg},
            {'role': 'assistant', 'content': assistant_msg}
        ]
    }


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    input_path = Path('training-artifacts/benchmark_jira.jsonl')
    output_path = script_dir / 'v14_multifile.jsonl'

    if not input_path.exists():
        print(f"❌ Error: {input_path} not found")
        return 1

    print(f"📂 Reading {input_path}...")
    print(f"🎯 Step 1: Grouping files by commit ID...")

    # Group files by commit ID
    commits = defaultdict(lambda: {'task': '', 'files': []})
    total_lines = 0

    with open(input_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue

            total_lines += 1
            try:
                data = json.loads(line)
                commit_id = data.get('id', '')
                task_desc = data.get('task_description', '')
                files = data.get('files', [])

                if commit_id and files:
                    commits[commit_id]['task'] = task_desc
                    commits[commit_id]['files'].extend(files)

            except Exception as e:
                print(f"   ⚠ Error reading line: {e}")

    print(f"   Read {total_lines} lines")
    print(f"   Found {len(commits)} unique commits")

    print(f"\n🎯 Step 2: Filtering and transforming...")
    print(f"   - Excluding Patch*.java files")
    print(f"   - Keeping commits with 3+ valid files")

    transformed = 0
    filtered_patch = 0
    filtered_small = 0
    filtered_other = 0

    with open(output_path, 'w') as f_out:
        for i, (commit_id, commit_info) in enumerate(commits.items()):
            try:
                task_desc = commit_info['task']
                files = commit_info['files']

                # Count Patch files
                patch_count = sum(1 for f in files if re.search(r'/Patch\d+\.java$', f.get('path', '')))
                filtered_patch += patch_count

                # Transform to training example
                example = transform_commit_to_example(commit_id, task_desc, files)

                if example:
                    f_out.write(json.dumps(example) + '\n')
                    transformed += 1
                else:
                    # Check why filtered
                    valid_files = [f for f in files if should_include_file(f.get('path', ''))]
                    if len(valid_files) < 3:
                        filtered_small += 1
                    else:
                        filtered_other += 1

                # Progress
                if (i + 1) % 500 == 0:
                    print(f"   Processed {i+1}/{len(commits)} commits, {transformed} transformed...")

            except Exception as e:
                print(f"   ⚠ Error processing commit {commit_id}: {e}")
                filtered_other += 1

    print(f"\n✅ Transformation complete!")
    print(f"   Total commits: {total}")
    print(f"   Transformed: {transformed}")
    print(f"   Filtered (Patch files): {filtered_patch}")
    print(f"   Filtered (<3 files): {filtered_small}")
    print(f"   Filtered (other): {filtered_other}")
    print(f"   Output: {output_path}")

    # Calculate stats
    if transformed > 0:
        print(f"\n📊 Dataset Statistics:")
        print(f"   Multi-file examples: {transformed}")
        print(f"   Avg files per example: ~4-10 (filtered for 3+)")
        print(f"   Patch*.java files removed: {filtered_patch}")

    return 0


if __name__ == '__main__':
    exit(main())

