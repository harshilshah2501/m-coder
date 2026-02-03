#!/usr/bin/env python3
"""
Multi-File Training Data Extractor for Motadata

CRITICAL DIFFERENCE from motadata_extractor.py:
- Keeps multi-file commits TOGETHER as single training examples
- Does NOT split commits into per-file examples
- Filters out Patch*.java files
- Prioritizes commits with 3+ files

This is the CORRECT way to extract training data for multi-file code generation.

Usage:
    python3 extract_multifile_training_data.py --repo /path/to/motadata --output v14_training.jsonl
"""

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass


@dataclass
class MultiFileCommit:
    """A commit with multiple file changes kept together."""
    commit_hash: str
    message: str
    files: List[Dict[str, str]]  # [{path, diff}, ...]
    
    
class MultiFileExtractor:
    """Extract multi-file commits from git repository."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.stats = {
            'commits_scanned': 0,
            'commits_matched': 0,
            'commits_multifile': 0,
            'files_total': 0,
            'files_filtered_patch': 0,
            'examples_created': 0
        }
    
    def run_git(self, args: List[str]) -> Optional[str]:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.stdout if result.returncode == 0 else None
        except Exception as e:
            print(f"   ⚠ Git error: {e}")
            return None
    
    def should_include_commit(self, message: str) -> bool:
        """Check if commit message indicates meaningful change."""
        # Exclude patterns
        exclude = [
            r'^[Mm]erge', r'^[Rr]evert', r'^[Ww]ip', r'^[Tt]emp',
            r'^[Bb]ump', r'^[Ii]nitial', r'^[Uu]pgrade'
        ]
        for pattern in exclude:
            if re.search(pattern, message):
                return False
        
        # Include patterns
        include = [
            r'^[Ff]ix', r'^[Bb]ug', r'^[Pp]atch', r'^[Ff]eat',
            r'^[Aa]dd', r'^[Ii]mplement', r'^[Rr]efactor',
            r'^[Uu]pdate', r'^[Oo]ptimize', r'MOTADATA-\d+', r'MOT-\d+'
        ]
        for pattern in include:
            if re.search(pattern, message):
                return True
        
        return False
    
    def should_include_file(self, path: str) -> bool:
        """Check if file should be included."""
        # Exclude Patch*.java files
        if re.search(r'/Patch\d+\.java$', path):
            self.stats['files_filtered_patch'] += 1
            return False
        
        # Only .java files
        if not path.endswith('.java'):
            return False
        
        # Exclude test files, build artifacts, etc.
        exclude_patterns = [
            r'Test\.java$', r'target/', r'build/', r'node_modules/',
            r'\.min\.', r'package-lock', r'yarn\.lock'
        ]
        for pattern in exclude_patterns:
            if re.search(pattern, path):
                return False
        
        return True
    
    def parse_commit_files(self, commit_hash: str) -> Optional[MultiFileCommit]:
        """Parse all files changed in a commit."""
        # Get commit message
        msg_output = self.run_git(['log', '-1', '--format=%s', commit_hash])
        if not msg_output:
            return None
        
        message = msg_output.strip()
        
        # Get full diff
        diff_output = self.run_git(['show', '--format=', commit_hash])
        if not diff_output:
            return None
        
        # Parse diff into per-file changes
        files = []
        current_file = None
        current_diff_lines = []
        
        for line in diff_output.split('\n'):
            # New file marker
            if line.startswith('diff --git'):
                # Save previous file
                if current_file and current_diff_lines:
                    diff_content = '\n'.join(current_diff_lines)
                    if re.search(r'@@\s+-\d+,\d+\s+\+\d+,\d+\s+@@', diff_content):
                        files.append({
                            'path': current_file,
                            'diff': diff_content
                        })
                
                # Extract file path
                match = re.search(r'b/(.+)$', line)
                current_file = match.group(1) if match else None
                current_diff_lines = []
            else:
                current_diff_lines.append(line)
        
        # Save last file
        if current_file and current_diff_lines:
            diff_content = '\n'.join(current_diff_lines)
            if re.search(r'@@\s+-\d+,\d+\s+\+\d+,\d+\s+@@', diff_content):
                files.append({
                    'path': current_file,
                    'diff': diff_content
                })
        
        # Filter files
        valid_files = [f for f in files if self.should_include_file(f['path'])]
        self.stats['files_total'] += len(files)
        
        if not valid_files:
            return None
        
        return MultiFileCommit(
            commit_hash=commit_hash,
            message=message,
            files=valid_files
        )

    def extract_from_branch(self, branch: str, max_commits: int = 2000) -> List[MultiFileCommit]:
        """Extract multi-file commits from a branch."""
        print(f"\n📌 Extracting from branch: {branch}")

        # Get commit list
        log_output = self.run_git(['log', branch, '--oneline', f'-{max_commits}'])
        if not log_output:
            print(f"   ⚠ Could not get log for {branch}")
            return []

        commits = []
        for line in log_output.strip().split('\n'):
            if line.strip():
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    commits.append((parts[0], parts[1]))

        print(f"   Found {len(commits)} commits")

        results = []
        for i, (commit_hash, commit_msg) in enumerate(commits):
            self.stats['commits_scanned'] += 1

            # Check if commit should be included
            if not self.should_include_commit(commit_msg):
                continue

            self.stats['commits_matched'] += 1

            # Parse commit
            multi_commit = self.parse_commit_files(commit_hash)
            if multi_commit and len(multi_commit.files) >= 3:
                results.append(multi_commit)
                self.stats['commits_multifile'] += 1

            # Progress
            if (i + 1) % 500 == 0:
                print(f"   Processed {i+1}/{len(commits)}, found {len(results)} multi-file commits...")

        print(f"   ✓ Extracted {len(results)} multi-file commits")
        return results

    def format_as_training_example(self, commit: MultiFileCommit) -> dict:
        """Format multi-file commit as training example."""
        # Create file list for user message
        file_list = '\n'.join([f"{i+1}. {f['path']}" for i, f in enumerate(commit.files)])

        # Create thinking block
        thinking = f"""<thinking>
**Task**: {commit.message}

**Files to modify** ({len(commit.files)} files):
{chr(10).join([f'- {f["path"]}' for f in commit.files])}

**Plan**:
1. Analyze the required changes across all files
2. Ensure consistency across the codebase
3. Apply changes in proper order
4. Maintain code quality and patterns

**Approach**: Generate unified diffs for each file with proper format.
</thinking>"""

        # Format all diffs
        formatted_diffs = []
        for file_info in commit.files:
            path = file_info['path']
            diff = file_info['diff']

            # Strip motadata/ prefix
            if path.startswith('motadata/'):
                path = path[len('motadata/'):]

            # Ensure proper diff headers
            if not re.search(r'---\s+a/', diff):
                diff = f"--- a/{path}\n+++ b/{path}\n{diff}"

            formatted = f"File: {path}\n```diff\n{diff.strip()}\n```"
            formatted_diffs.append(formatted)

        code_block = '\n\n'.join(formatted_diffs)

        # System message
        system_msg = """You are a senior Motadata engineer. Given a task and multiple files to modify, generate precise unified diffs for each file.

CRITICAL REQUIREMENTS:
- Generate diffs for ALL files listed in the task
- Use proper unified diff format with --- a/ and +++ b/ headers
- Include File: prefix for each file
- Wrap each diff in ```diff blocks
- Ensure changes are consistent across all files"""

        # User message
        user_msg = f"""Task: {commit.message}

Files to modify ({len(commit.files)} files):
{file_list}

Generate unified diffs for all files to implement this change."""

        # Assistant message
        assistant_msg = f"{thinking}\n\n<code>\n{code_block}\n</code>"

        return {
            'messages': [
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': user_msg},
                {'role': 'assistant', 'content': assistant_msg}
            ]
        }

    def extract_and_save(self, branches: List[str], output_path: str, max_commits: int = 2000):
        """Extract from branches and save to JSONL."""
        print(f"\n{'='*60}")
        print(f"Multi-File Training Data Extraction")
        print(f"Repository: {self.repo_path}")
        print(f"Branches: {', '.join(branches)}")
        print(f"Output: {output_path}")
        print(f"{'='*60}")

        all_commits = []
        seen_hashes = set()

        for branch in branches:
            commits = self.extract_from_branch(branch, max_commits)

            # Deduplicate
            for commit in commits:
                if commit.commit_hash not in seen_hashes:
                    all_commits.append(commit)
                    seen_hashes.add(commit.commit_hash)

        print(f"\n📊 Total unique multi-file commits: {len(all_commits)}")

        # Convert to training examples and save
        print(f"\n💾 Saving to {output_path}...")
        with open(output_path, 'w') as f:
            for commit in all_commits:
                example = self.format_as_training_example(commit)
                f.write(json.dumps(example) + '\n')
                self.stats['examples_created'] += 1

        print(f"\n✅ Extraction complete!")
        print(f"\n📊 Statistics:")
        print(f"   Commits scanned: {self.stats['commits_scanned']}")
        print(f"   Commits matched: {self.stats['commits_matched']}")
        print(f"   Multi-file commits (3+): {self.stats['commits_multifile']}")
        print(f"   Files total: {self.stats['files_total']}")
        print(f"   Files filtered (Patch*.java): {self.stats['files_filtered_patch']}")
        print(f"   Training examples created: {self.stats['examples_created']}")


def main():
    parser = argparse.ArgumentParser(description='Extract multi-file training data from Motadata repo')
    parser.add_argument('--repo', required=True, help='Path to Motadata repository')
    parser.add_argument('--output', default='v14_training.jsonl', help='Output JSONL file')
    parser.add_argument('--branches', nargs='+', default=['develop'], help='Branches to extract from')
    parser.add_argument('--max-commits', type=int, default=2000, help='Max commits per branch')

    args = parser.parse_args()

    extractor = MultiFileExtractor(args.repo)
    extractor.extract_and_save(args.branches, args.output, args.max_commits)


if __name__ == '__main__':
    main()

