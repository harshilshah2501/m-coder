#!/usr/bin/env python3
"""
Motadata Fine-Tuning Data Extractor (Multi-Branch)

Extracts (Original File, Commit Message, Diff) tuples from git history.
Supports single repository with multiple branches (GA releases + development).

Run this on your LOCAL machine with git access.

Usage:
    python motadata_extractor.py --config extraction_config.yaml --output data.jsonl
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import yaml

@dataclass
class TrainingExample:
    """Single training example for fine-tuning."""
    repo_name: str
    branch: str
    commit_hash: str
    commit_message: str
    file_path: str
    original_content: str
    diff_content: str
    hunks: int
    lines_added: int
    lines_removed: int
    timestamp: str

    # Pre-formatted for training
    system_prompt: str
    user_prompt: str
    assistant_response: str

class MotadataExtractor:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.seen_commits: Set[str] = set()  # For deduplication
        self.stats = {
            'branches_processed': 0,
            'commits_scanned': 0,
            'commits_matched': 0,
            'commits_deduplicated': 0,
            'files_extracted': 0,
            'files_filtered': 0,
            'errors': 0
        }

    def _load_config(self, path: str) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)
    
    def _run_git(self, repo_path: str, args: List[str], timeout: int = 30) -> Optional[str]:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception as e:
            self.stats['errors'] += 1
            return None
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any pattern."""
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _should_include_commit(self, message: str) -> bool:
        """Check if commit should be included based on message."""
        filters = self.config['filters']
        
        # Check exclude patterns first
        if self._matches_patterns(message, filters.get('exclude_commit_patterns', [])):
            return False
        
        # Check include patterns
        if self._matches_patterns(message, filters.get('include_commit_patterns', [])):
            return True
        
        return False
    
    def _should_include_file(self, file_path: str) -> bool:
        """Check if file should be included based on path/extension."""
        filters = self.config['filters']
        
        # Check exclude paths
        for pattern in filters.get('exclude_paths', []):
            if re.search(pattern, file_path):
                return False
        
        # Check include extensions
        include_exts = filters.get('include_extensions', [])
        if include_exts:
            if not any(file_path.endswith(ext) for ext in include_exts):
                return False
        
        return True
    
    def _count_hunks(self, diff: str) -> int:
        """Count hunks in diff."""
        return len(re.findall(r'^@@', diff, re.MULTILINE))
    
    def _count_lines(self, diff: str) -> Tuple[int, int]:
        """Count added and removed lines."""
        added = len([l for l in diff.split('\n') if l.startswith('+') and not l.startswith('+++')])
        removed = len([l for l in diff.split('\n') if l.startswith('-') and not l.startswith('---')])
        return added, removed
    
    def _get_file_at_commit(self, repo_path: str, commit: str, file_path: str) -> Optional[str]:
        """Get file content at specific commit (before the change)."""
        # Get parent commit
        parent = f"{commit}^"
        return self._run_git(repo_path, ['show', f'{parent}:{file_path}'])
    
    def _get_commit_diff(self, repo_path: str, commit: str) -> Optional[str]:
        """Get diff for a specific commit."""
        return self._run_git(repo_path, ['show', '--format=', commit])
    
    def _parse_diff(self, diff_output: str) -> Dict[str, str]:
        """Parse diff output into per-file diffs."""
        files = {}
        current_file = None
        current_lines = []
        
        for line in diff_output.split('\n'):
            if line.startswith('diff --git'):
                if current_file and current_lines:
                    files[current_file] = '\n'.join(current_lines)
                match = re.search(r'b/(.+)$', line)
                current_file = match.group(1) if match else None
                current_lines = []
            elif current_file:
                current_lines.append(line)
        
        if current_file and current_lines:
            files[current_file] = '\n'.join(current_lines)
        
        return files
    
    def _format_training_example(
        self,
        repo_name: str,
        branch: str,
        commit_hash: str,
        commit_message: str,
        file_path: str,
        original_content: str,
        diff_content: str
    ) -> Optional[TrainingExample]:
        """Format as training example."""
        filters = self.config['filters']
        
        # Count metrics
        hunks = self._count_hunks(diff_content)
        added, removed = self._count_lines(diff_content)
        total_lines = added + removed
        
        # Apply size filters
        if total_lines < filters.get('min_diff_lines', 2):
            return None
        if total_lines > filters.get('max_diff_lines', 100):
            return None
        if hunks > filters.get('max_hunks', 5):
            return None
        
        # Check file size
        if original_content:
            file_lines = len(original_content.split('\n'))
            if file_lines > filters.get('max_file_lines', 500):
                return None
        
        # Format prompts
        system_prompt = self.config['output'].get('system_prompt', '').strip()
        
        user_prompt = f"""File: {file_path}

Content:
```
{original_content}
```

Task: {commit_message}

Generate the unified diff to implement this change."""
        
        assistant_response = f"""```diff
{diff_content}
```"""
        
        return TrainingExample(
            repo_name=repo_name,
            branch=branch,
            commit_hash=commit_hash,
            commit_message=commit_message,
            file_path=file_path,
            original_content=original_content,
            diff_content=diff_content,
            hunks=hunks,
            lines_added=added,
            lines_removed=removed,
            timestamp=datetime.now().isoformat(),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            assistant_response=assistant_response
        )

    def _get_all_branches(self) -> List[Tuple[str, int]]:
        """Get all branches to process with their priorities."""
        branches_config = self.config.get('branches', {})
        priority_config = branches_config.get('priority', {})

        branches = []

        # GA releases (highest priority)
        for branch in branches_config.get('ga_releases', []):
            branches.append((branch, priority_config.get('ga_releases', 3)))

        # Development branches
        for branch in branches_config.get('development', []):
            branches.append((branch, priority_config.get('development', 2)))

        # Feature branches (lowest priority)
        for branch in branches_config.get('feature', []):
            branches.append((branch, priority_config.get('feature', 1)))

        # Sort by priority (higher first)
        return sorted(branches, key=lambda x: -x[1])

    def _get_remote_branch(self, branch: str) -> str:
        """Get the remote branch reference (origin/branch)."""
        if branch.startswith('origin/'):
            return branch
        return f"origin/{branch}"

    def extract_from_branch(self, repo_path: str, repo_name: str, branch: str) -> List[TrainingExample]:
        """Extract training examples from a single branch (without checkout)."""
        print(f"\n  📌 Branch: {branch}")

        # Use remote branch reference - no checkout needed!
        remote_branch = self._get_remote_branch(branch)

        examples = []
        history_config = self.config.get('history', {})
        max_commits = history_config.get('max_commits_per_branch', 2000)
        deduplicate = history_config.get('deduplicate', True)

        # Get commit list from remote branch directly
        git_log_args = ['log', remote_branch, '--oneline', f'-{max_commits}']

        if history_config.get('since_date'):
            git_log_args.extend(['--since', history_config['since_date']])
        if history_config.get('until_date'):
            git_log_args.extend(['--until', history_config['until_date']])

        log_output = self._run_git(repo_path, git_log_args, timeout=60)
        if not log_output:
            print(f"     ⚠ Could not get git log for {remote_branch}")
            return []

        commits = []
        for line in log_output.strip().split('\n'):
            if line.strip():
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    commits.append((parts[0], parts[1]))

        print(f"     Found {len(commits)} commits")

        matched = 0
        for i, (commit_hash, commit_msg) in enumerate(commits):
            self.stats['commits_scanned'] += 1

            # Deduplication: skip if already seen in another branch
            if deduplicate and commit_hash in self.seen_commits:
                self.stats['commits_deduplicated'] += 1
                continue

            # Progress indicator
            if (i + 1) % 500 == 0:
                print(f"     Processed {i+1}/{len(commits)} commits, {matched} matched...")

            # Check if commit should be included
            if not self._should_include_commit(commit_msg):
                continue

            self.stats['commits_matched'] += 1
            self.seen_commits.add(commit_hash)
            matched += 1

            # Get diff for this commit
            diff_output = self._get_commit_diff(repo_path, commit_hash)
            if not diff_output:
                continue

            # Parse into per-file diffs
            file_diffs = self._parse_diff(diff_output)

            for file_path, diff_content in file_diffs.items():
                # Check if file should be included
                if not self._should_include_file(file_path):
                    self.stats['files_filtered'] += 1
                    continue

                # Get original file content
                original_content = self._get_file_at_commit(repo_path, commit_hash, file_path)
                if not original_content:
                    continue

                # Format as training example
                example = self._format_training_example(
                    repo_name=repo_name,
                    branch=branch,
                    commit_hash=commit_hash,
                    commit_message=commit_msg,
                    file_path=file_path,
                    original_content=original_content,
                    diff_content=diff_content
                )

                if example:
                    examples.append(example)
                    self.stats['files_extracted'] += 1
                else:
                    self.stats['files_filtered'] += 1

        print(f"     ✓ Extracted {len(examples)} examples from {branch}")
        self.stats['branches_processed'] += 1

        return examples

    def extract_all(self) -> List[TrainingExample]:
        """Extract from all configured branches."""
        repo_config = self.config.get('repository', {})
        repo_path = repo_config.get('path', '')
        repo_name = repo_config.get('name', 'motadata')

        print(f"\n{'='*60}")
        print(f"Repository: {repo_name}")
        print(f"Path: {repo_path}")
        print('='*60)

        if not os.path.exists(repo_path):
            print(f"⚠ Repository not found: {repo_path}")
            return []

        all_examples = []
        branches = self._get_all_branches()

        print(f"\nBranches to process: {len(branches)}")
        for branch, priority in branches:
            print(f"  - {branch} (priority: {priority})")

        for branch, priority in branches:
            examples = self.extract_from_branch(repo_path, repo_name, branch)
            all_examples.extend(examples)

        return all_examples

    def save_to_jsonl(self, examples: List[TrainingExample], output_path: str):
        """Save examples to JSONL file."""
        print(f"\nSaving {len(examples)} examples to {output_path}...")

        with open(output_path, 'w') as f:
            for ex in examples:
                # Training format (OpenAI compatible)
                training_record = {
                    "messages": [
                        {"role": "system", "content": ex.system_prompt},
                        {"role": "user", "content": ex.user_prompt},
                        {"role": "assistant", "content": ex.assistant_response}
                    ],
                    "metadata": {
                        "repo": ex.repo_name,
                        "branch": ex.branch,
                        "commit": ex.commit_hash,
                        "file": ex.file_path,
                        "hunks": ex.hunks,
                        "lines_added": ex.lines_added,
                        "lines_removed": ex.lines_removed
                    }
                }
                f.write(json.dumps(training_record) + '\n')

        print(f"✓ Saved to {output_path}")

    def print_stats(self):
        """Print extraction statistics."""
        print("\n" + "="*70)
        print("EXTRACTION STATISTICS")
        print("="*70)
        print(f"  Branches processed: {self.stats['branches_processed']}")
        print(f"  Commits scanned: {self.stats['commits_scanned']}")
        print(f"  Commits matched: {self.stats['commits_matched']}")
        print(f"  Commits deduplicated: {self.stats['commits_deduplicated']}")
        print(f"  Files extracted: {self.stats['files_extracted']}")
        print(f"  Files filtered: {self.stats['files_filtered']}")
        print(f"  Errors: {self.stats['errors']}")
        print("="*70)


def main():
    parser = argparse.ArgumentParser(description='Extract Motadata fine-tuning data')
    parser.add_argument('--config', default='extraction_config.yaml', help='Config file path')
    parser.add_argument('--output', default='motadata_finetuning_data.jsonl', help='Output file')
    args = parser.parse_args()

    print("="*60)
    print("MOTADATA FINE-TUNING DATA EXTRACTOR")
    print("="*60)

    extractor = MotadataExtractor(args.config)
    examples = extractor.extract_all()

    if examples:
        extractor.save_to_jsonl(examples, args.output)
    else:
        print("\n⚠ No examples extracted!")

    extractor.print_stats()

    # Summary
    print(f"\n✅ Done! Extracted {len(examples)} training examples")
    if len(examples) >= 500:
        print("   Target of 500+ examples: ACHIEVED ✓")
    else:
        print(f"   Target of 500+ examples: Need {500 - len(examples)} more")


if __name__ == '__main__':
    main()

