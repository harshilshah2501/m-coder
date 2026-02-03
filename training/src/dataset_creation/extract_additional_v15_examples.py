#!/usr/bin/env python3
"""
Extract additional examples for V15 from benchmark_jira.jsonl.

We need:
- Multi-file: 192 more (to reach 300)
- Code review: 300 (generate from commits)
- File creation: 130 more (to reach 150)
- Refactoring: 50 (from commits with "refactor")

Usage:
    python3 extract_additional_v15_examples.py
"""

import json
from pathlib import Path
from typing import List, Dict
import re
from collections import defaultdict

JIRA_FILE = Path("training-artifacts/benchmark_jira.jsonl")
OUTPUT_FILE = Path("evaluation/finetuning/v15_additional.jsonl")

# System message for all examples
SYSTEM_MSG = """You are a senior Motadata engineer. Given a task and files to modify, generate precise unified diffs for each file.
Always use proper unified diff format with --- a/, +++ b/, and @@ headers."""


def group_by_commit(jira_file: Path) -> Dict[str, List[dict]]:
    """Group files by commit ID."""
    commits = defaultdict(list)
    
    print(f"📂 Loading {jira_file}...")
    
    with open(jira_file) as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                commit_id = data.get('id', '')
                files = data.get('files', [])
                task = data.get('task_description', '')
                
                if commit_id and files:
                    commits[commit_id].append({
                        'task': task,
                        'files': files
                    })
            except Exception as e:
                continue
    
    print(f"✅ Found {len(commits)} unique commits")
    return commits


def create_multifile_example(commit_id: str, task: str, files: List[dict]) -> dict:
    """Create a multi-file training example."""
    # Filter valid files
    valid_files = []
    for f in files:
        path = f.get('path', '')
        diff = f.get('expected_diff', '')
        
        # Skip Patch files
        if re.search(r'/Patch\d+\.java$', path):
            continue
        
        # Must have valid diff
        if not diff or '@@' not in diff:
            continue
        
        valid_files.append({'path': path, 'diff': diff})
    
    if len(valid_files) < 3:
        return None
    
    # Create thinking block
    file_list = '\n'.join([f"{i+1}. {f['path']}" for i, f in enumerate(valid_files)])
    thinking = f"""<thinking>
I need to modify {len(valid_files)} files to implement: {task}

Files to change:
{file_list}

I'll generate unified diffs for each file with proper format.
</thinking>"""
    
    # Format diffs
    formatted_diffs = []
    for f in valid_files:
        formatted_diffs.append(f"File: {f['path']}\n```diff\n{f['diff']}\n```")
    
    assistant_msg = f"{thinking}\n\n<code>\n" + "\n\n".join(formatted_diffs) + "\n</code>"
    
    # User message
    user_msg = f"""Task: {task}

Files to modify ({len(valid_files)} files):
{file_list}

Generate unified diffs for all files to implement this change."""
    
    return {
        'messages': [
            {'role': 'system', 'content': SYSTEM_MSG},
            {'role': 'user', 'content': user_msg},
            {'role': 'assistant', 'content': assistant_msg}
        ],
        'metadata': {
            'commit': commit_id,
            'files_count': len(valid_files),
            'category': 'multi_file'
        }
    }


def create_file_creation_example(commit_id: str, task: str, files: List[dict]) -> dict:
    """Create a file creation example (has /dev/null in diff)."""
    # Find files with /dev/null (new files)
    new_files = []
    for f in files:
        path = f.get('path', '')
        diff = f.get('expected_diff', '')
        
        if '/dev/null' in diff or '--- /dev/null' in diff:
            new_files.append({'path': path, 'diff': diff})
    
    if not new_files:
        return None
    
    # Create example
    file_list = '\n'.join([f"{i+1}. {f['path']}" for i, f in enumerate(new_files)])
    thinking = f"""<thinking>
I need to create {len(new_files)} new file(s) for: {task}

New files:
{file_list}

I'll generate diffs showing file creation.
</thinking>"""
    
    formatted_diffs = []
    for f in new_files:
        formatted_diffs.append(f"File: {f['path']}\n```diff\n{f['diff']}\n```")
    
    assistant_msg = f"{thinking}\n\n<code>\n" + "\n\n".join(formatted_diffs) + "\n</code>"
    
    user_msg = f"""Task: {task}

Create new file(s):
{file_list}

Generate unified diffs for file creation."""
    
    return {
        'messages': [
            {'role': 'system', 'content': SYSTEM_MSG},
            {'role': 'user', 'content': user_msg},
            {'role': 'assistant', 'content': assistant_msg}
        ],
        'metadata': {
            'commit': commit_id,
            'files_count': len(new_files),
            'category': 'file_creation'
        }
    }


def create_refactoring_example(commit_id: str, task: str, files: List[dict]) -> dict:
    """Create a refactoring example."""
    # Only if task mentions refactoring
    if not any(word in task.lower() for word in ['refactor', 'cleanup', 'optimize', 'improve']):
        return None
    
    valid_files = []
    for f in files:
        path = f.get('path', '')
        diff = f.get('expected_diff', '')
        
        if diff and '@@' in diff:
            valid_files.append({'path': path, 'diff': diff})
    
    if not valid_files:
        return None
    
    file_list = '\n'.join([f"{i+1}. {f['path']}" for i, f in enumerate(valid_files)])
    thinking = f"""<thinking>
Refactoring task: {task}

Files to refactor:
{file_list}

I'll apply code quality improvements.
</thinking>"""
    
    formatted_diffs = []
    for f in valid_files:
        formatted_diffs.append(f"File: {f['path']}\n```diff\n{f['diff']}\n```")
    
    assistant_msg = f"{thinking}\n\n<code>\n" + "\n\n".join(formatted_diffs) + "\n</code>"
    
    user_msg = f"""Task: {task}

Files to refactor:
{file_list}"""
    
    return {
        'messages': [
            {'role': 'system', 'content': SYSTEM_MSG},
            {'role': 'user', 'content': user_msg},
            {'role': 'assistant', 'content': assistant_msg}
        ],
        'metadata': {
            'commit': commit_id,
            'files_count': len(valid_files),
            'category': 'refactoring'
        }
    }


def main():
    """Main extraction."""
    print("=" * 60)
    print("V15 Additional Examples Extractor")
    print("=" * 60)

    # Group by commit
    commits = group_by_commit(JIRA_FILE)

    # Extract examples
    multifile_examples = []
    file_creation_examples = []
    refactoring_examples = []

    print("\n📊 Extracting examples...")

    for commit_id, commit_data in commits.items():
        for data in commit_data:
            task = data['task']
            files = data['files']

            # Try multi-file
            example = create_multifile_example(commit_id, task, files)
            if example:
                multifile_examples.append(example)

            # Try file creation
            example = create_file_creation_example(commit_id, task, files)
            if example:
                file_creation_examples.append(example)

            # Try refactoring
            example = create_refactoring_example(commit_id, task, files)
            if example:
                refactoring_examples.append(example)

    print(f"\n✅ Extracted:")
    print(f"  Multi-file: {len(multifile_examples)}")
    print(f"  File creation: {len(file_creation_examples)}")
    print(f"  Refactoring: {len(refactoring_examples)}")

    # Write output
    print(f"\n📝 Writing to {OUTPUT_FILE}...")

    with open(OUTPUT_FILE, 'w') as f:
        for example in multifile_examples:
            f.write(json.dumps(example) + '\n')
        for example in file_creation_examples:
            f.write(json.dumps(example) + '\n')
        for example in refactoring_examples:
            f.write(json.dumps(example) + '\n')

    total = len(multifile_examples) + len(file_creation_examples) + len(refactoring_examples)
    print(f"✅ Wrote {total} examples")

    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print("1. Re-run: python3 evaluation/finetuning/create_v15_balanced_dataset.py")
    print("2. This will include the new examples")

    return 0


if __name__ == '__main__':
    exit(main())

