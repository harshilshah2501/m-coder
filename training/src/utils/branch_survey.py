#!/usr/bin/env python3
"""
Branch Survey Tool for Motadata Fine-Tuning Data Extraction

This tool analyzes all branches in the repository and recommends:
1. Top branches with the most relevant commits
2. Optimal branch selection to maximize unique training examples
3. Deduplication statistics across branches

Usage:
    python branch_survey.py --repo /path/to/motadata-repo --output branch_analysis.json
"""

import argparse
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple


class BranchSurveyor:
    """Survey git branches to find optimal extraction targets"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"Repository not found: {repo_path}")
        
        # Default filters (same as extraction_config.yaml)
        self.include_patterns = [
            r"^[Ff]ix", r"^[Bb]ug", r"^[Pp]atch", r"^[Ff]eat",
            r"^[Aa]dd", r"^[Ii]mplement", r"^[Rr]efactor",
            r"^[Uu]pdate", r"^[Oo]ptimize",
            r"MOTADATA-[0-9]+", r"MOT-[0-9]+"
        ]
        
        self.exclude_patterns = [
            r"^[Ww]ip", r"^[Tt]emp", r"^[Mm]erge",
            r"^[Rr]evert", r"^[Bb]ump", r"^[Uu]pgrade", r"^[Ii]nitial"
        ]
        
        self.file_extensions = [".java", ".py", ".yaml", ".yml", ".json", ".xml", ".properties"]
    
    def run_git_command(self, cmd: List[str]) -> str:
        """Run git command and return output"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Git command failed: {' '.join(cmd)}")
            print(f"   Error: {e.stderr}")
            return ""
    
    def get_all_branches(self, filter_mode: str = 'all') -> List[str]:
        """Get all branches (local + remote)"""
        print("🔍 Discovering all branches...")
        
        # Get remote branches
        output = self.run_git_command(["git", "branch", "-r"])
        branches = []
        
        for line in output.split('\n'):
            line = line.strip()
            if not line or '->' in line:  # Skip HEAD pointers
                continue
            
            # Remove 'origin/' prefix
            branch = line.replace('origin/', '')
            branches.append(branch)
        
        print(f"   Found {len(branches)} total branches")
        
        # Apply filtering
        if filter_mode == 'ga-and-master':
            filtered = []
            for branch in branches:
                # Include master/main/develop
                if branch in ['master', 'main', 'develop', 'development']:
                    filtered.append(branch)
                # Include release branches: release/X.Y pattern
                elif re.match(r'release/\d+\.\d+', branch):
                    filtered.append(branch)
                # Include Motadata-style releases: *_upgrade_release or *_release with version
                elif '_release' in branch.lower() and re.search(r'\d+\.\d+\.\d+', branch):
                    filtered.append(branch)
            print(f"   Filtered to {len(filtered)} branches (releases + master)")
            return sorted(set(filtered))
        
        return sorted(set(branches))
    
    def categorize_branches(self, branches: List[str]) -> Dict[str, List[str]]:
        """Categorize branches by type"""
        categories = {
            'ga_releases': [],
            'development': [],
            'feature': [],
            'hotfix': [],
            'other': []
        }
        
        for branch in branches:
            if re.match(r'release/\d+\.\d+', branch):
                categories['ga_releases'].append(branch)
            elif branch in ['main', 'master', 'develop', 'development']:
                categories['development'].append(branch)
            elif branch.startswith('feature/'):
                categories['feature'].append(branch)
            elif branch.startswith('hotfix/'):
                categories['hotfix'].append(branch)
            else:
                categories['other'].append(branch)
        
        return categories
    
    def matches_commit_filter(self, message: str) -> bool:
        """Check if commit message matches filters"""
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if re.search(pattern, message):
                return False
        
        # Check include patterns
        for pattern in self.include_patterns:
            if re.search(pattern, message):
                return True
        
        return False
    
    def analyze_branch(self, branch: str, max_commits: int = 2000) -> Dict:
        """Analyze a single branch for relevant commits (without checkout)"""
        print(f"   📊 Analyzing: {branch}")
        
        # Use origin/branch directly - no checkout needed!
        remote_branch = f"origin/{branch}"
        
        # Get commit log from remote branch directly
        log_output = self.run_git_command([
            "git", "log",
            remote_branch,
            f"-{max_commits}",
            "--pretty=format:%H|%s|%an|%ad",
            "--date=short"
        ])
        
        if not log_output:
            return {
                'branch': branch,
                'total_commits': 0,
                'relevant_commits': 0,
                'commit_hashes': set(),
                'last_commit_date': None,
                'authors': set(),
                'file_types': defaultdict(int)
            }
        
        commits = log_output.split('\n')
        relevant_commits = []
        commit_hashes = set()
        authors = set()
        file_types = defaultdict(int)
        
        for commit_line in commits:
            if not commit_line:
                continue
            
            parts = commit_line.split('|')
            if len(parts) < 4:
                continue
            
            commit_hash, message, author, date = parts[0], parts[1], parts[2], parts[3]
            commit_hashes.add(commit_hash)
            
            if self.matches_commit_filter(message):
                relevant_commits.append(commit_hash)
                authors.add(author)
                
                # Analyze files in this commit
                files_output = self.run_git_command([
                    "git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash
                ])
                
                for file_path in files_output.split('\n'):
                    if file_path:
                        ext = Path(file_path).suffix
                        if ext in self.file_extensions:
                            file_types[ext] += 1
        
        # Get last commit date
        last_commit_date = None
        if commits:
            last_commit_date = commits[0].split('|')[3] if '|' in commits[0] else None
        
        return {
            'branch': branch,
            'total_commits': len(commits),
            'relevant_commits': len(relevant_commits),
            'commit_hashes': commit_hashes,
            'relevant_commit_hashes': set(relevant_commits),
            'last_commit_date': last_commit_date,
            'authors': authors,
            'file_types': dict(file_types)
        }
    
    def calculate_overlap(self, branch_analyses: List[Dict]) -> Dict:
        """Calculate commit overlap between branches"""
        print("\n🔄 Calculating cross-branch overlap...")
        
        # Build commit -> branches mapping
        commit_to_branches = defaultdict(set)
        
        for analysis in branch_analyses:
            branch = analysis['branch']
            for commit in analysis['relevant_commit_hashes']:
                commit_to_branches[commit].add(branch)
        
        # Calculate unique commits per branch
        overlap_stats = {}
        
        for analysis in branch_analyses:
            branch = analysis['branch']
            total_relevant = len(analysis['relevant_commit_hashes'])
            
            # Count unique commits (only in this branch)
            unique_commits = sum(
                1 for commit in analysis['relevant_commit_hashes']
                if len(commit_to_branches[commit]) == 1
            )
            
            # Count shared commits
            shared_commits = total_relevant - unique_commits
            
            overlap_stats[branch] = {
                'total_relevant': total_relevant,
                'unique_commits': unique_commits,
                'shared_commits': shared_commits,
                'uniqueness_ratio': unique_commits / total_relevant if total_relevant > 0 else 0
            }
        
        return overlap_stats
    
    def recommend_branches(self, branch_analyses: List[Dict], overlap_stats: Dict, target: int = 500) -> List[str]:
        """Recommend optimal branch selection to maximize unique examples"""
        print(f"\n🎯 Recommending branches to reach {target}+ examples...")
        
        # Score each branch
        scored_branches = []
        
        for analysis in branch_analyses:
            branch = analysis['branch']
            
            # Skip branches with no relevant commits
            if analysis['relevant_commits'] == 0:
                continue
            
            overlap = overlap_stats.get(branch, {})
            
            # Scoring factors:
            # 1. Number of relevant commits (40%)
            # 2. Uniqueness ratio (30%)
            # 3. Recency (20%)
            # 4. File type diversity (10%)
            
            relevant_score = min(analysis['relevant_commits'] / 200, 1.0) * 0.4
            uniqueness_score = overlap.get('uniqueness_ratio', 0) * 0.3
            
            # Recency score
            recency_score = 0
            if analysis['last_commit_date']:
                try:
                    last_date = datetime.strptime(analysis['last_commit_date'], '%Y-%m-%d')
                    days_old = (datetime.now() - last_date).days
                    recency_score = max(0, 1 - (days_old / 730)) * 0.2  # 2 years = 0
                except:
                    pass
            
            # File type diversity score
            diversity_score = min(len(analysis['file_types']) / 5, 1.0) * 0.1
            
            total_score = relevant_score + uniqueness_score + recency_score + diversity_score
            
            scored_branches.append({
                'branch': branch,
                'score': total_score,
                'relevant_commits': analysis['relevant_commits'],
                'unique_commits': overlap.get('unique_commits', 0),
                'last_commit_date': analysis['last_commit_date']
            })
        
        # Sort by score
        scored_branches.sort(key=lambda x: x['score'], reverse=True)
        
        # Greedy selection to reach target
        selected = []
        total_unique = 0
        
        for branch_info in scored_branches:
            selected.append(branch_info['branch'])
            total_unique += branch_info['unique_commits']
            
            if total_unique >= target:
                break
        
        return selected
    
    def generate_report(self, branch_analyses: List[Dict], overlap_stats: Dict, recommended: List[str]) -> Dict:
        """Generate comprehensive survey report"""
        
        # Category breakdown
        all_branches = [a['branch'] for a in branch_analyses]
        categories = self.categorize_branches(all_branches)
        
        report = {
            'survey_date': datetime.now().isoformat(),
            'repository': str(self.repo_path),
            'total_branches': len(branch_analyses),
            'categories': {
                cat: len(branches) for cat, branches in categories.items()
            },
            'top_branches': [],
            'recommended_branches': recommended,
            'estimated_examples': 0,
            'branch_details': []
        }
        
        # Sort by relevant commits
        sorted_analyses = sorted(
            branch_analyses,
            key=lambda x: x['relevant_commits'],
            reverse=True
        )
        
        # Top 20 branches
        for analysis in sorted_analyses[:20]:
            branch = analysis['branch']
            overlap = overlap_stats.get(branch, {})
            
            report['top_branches'].append({
                'branch': branch,
                'total_commits': analysis['total_commits'],
                'relevant_commits': analysis['relevant_commits'],
                'unique_commits': overlap.get('unique_commits', 0),
                'shared_commits': overlap.get('shared_commits', 0),
                'uniqueness_ratio': f"{overlap.get('uniqueness_ratio', 0):.1%}",
                'last_commit_date': analysis['last_commit_date'],
                'file_types': analysis['file_types']
            })
        
        # Estimate examples from recommended branches
        for branch in recommended:
            overlap = overlap_stats.get(branch, {})
            report['estimated_examples'] += overlap.get('unique_commits', 0)
        
        # Full branch details
        for analysis in sorted_analyses:
            branch = analysis['branch']
            overlap = overlap_stats.get(branch, {})
            
            report['branch_details'].append({
                'branch': branch,
                'total_commits': analysis['total_commits'],
                'relevant_commits': analysis['relevant_commits'],
                'unique_commits': overlap.get('unique_commits', 0),
                'uniqueness_ratio': overlap.get('uniqueness_ratio', 0),
                'last_commit_date': analysis['last_commit_date']
            })
        
        return report
    
    def survey(self, max_commits_per_branch: int = 2000, target_examples: int = 500, filter_mode: str = 'all') -> Dict:
        """Run complete branch survey"""
        print("=" * 70)
        print("MOTADATA BRANCH SURVEY")
        print("=" * 70)
        print(f"Repository: {self.repo_path}")
        print(f"Target: {target_examples}+ training examples")
        if filter_mode == 'ga-and-master':
            print(f"Filter: GA releases + master only")
        print("=" * 70)
        
        # Get all branches
        branches = self.get_all_branches(filter_mode)
        
        if not branches:
            print("❌ No branches found!")
            return {}
        
        # Categorize
        categories = self.categorize_branches(branches)
        print(f"\n📂 Branch Categories:")
        for cat, cat_branches in categories.items():
            if cat_branches:
                print(f"   {cat}: {len(cat_branches)}")
        
        # Analyze each branch
        print(f"\n🔬 Analyzing {len(branches)} branches...")
        branch_analyses = []
        
        for branch in branches:
            try:
                analysis = self.analyze_branch(branch, max_commits_per_branch)
                branch_analyses.append(analysis)
            except Exception as e:
                print(f"   ⚠️  Failed to analyze {branch}: {e}")
        
        # Calculate overlap
        overlap_stats = self.calculate_overlap(branch_analyses)
        
        # Recommend branches
        recommended = self.recommend_branches(branch_analyses, overlap_stats, target_examples)
        
        # Generate report
        report = self.generate_report(branch_analyses, overlap_stats, recommended)
        
        # Print summary
        print("\n" + "=" * 70)
        print("SURVEY RESULTS")
        print("=" * 70)
        print(f"\n✅ Recommended {len(recommended)} branches:")
        for i, branch in enumerate(recommended, 1):
            overlap = overlap_stats.get(branch, {})
            print(f"   {i}. {branch}")
            print(f"      - Relevant commits: {overlap.get('total_relevant', 0)}")
            print(f"      - Unique commits: {overlap.get('unique_commits', 0)}")
            print(f"      - Uniqueness: {overlap.get('uniqueness_ratio', 0):.1%}")
        
        print(f"\n📊 Estimated unique examples: {report['estimated_examples']}")
        
        if report['estimated_examples'] >= target_examples:
            print(f"✅ Target of {target_examples}+ examples: ACHIEVABLE")
        else:
            print(f"⚠️  May need to adjust filters or add more branches")
        
        print("=" * 70)
        
        return report


def main():
    parser = argparse.ArgumentParser(description="Survey git branches for fine-tuning data extraction")
    parser.add_argument("--repo", required=True, help="Path to git repository")
    parser.add_argument("--output", default="branch_analysis.json", help="Output JSON file")
    parser.add_argument("--max-commits", type=int, default=2000, help="Max commits per branch")
    parser.add_argument("--target", type=int, default=500, help="Target number of examples")
    parser.add_argument("--filter-branches", choices=['all', 'ga-and-master'], default='all',
                        help="Filter branches: 'all' or 'ga-and-master' (GA releases + master only)")
    
    args = parser.parse_args()
    
    # Run survey
    surveyor = BranchSurveyor(args.repo)
    report = surveyor.survey(args.max_commits, args.target, args.filter_branches)
    
    # Save report
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Full report saved to: {output_path}")
    
    # Generate updated config
    config_path = output_path.parent / "recommended_config.yaml"
    generate_config(report, config_path)
    print(f"📝 Recommended config saved to: {config_path}")


def generate_config(report: Dict, output_path: Path):
    """Generate extraction_config.yaml with recommended branches"""
    
    recommended = report.get('recommended_branches', [])
    
    # Categorize recommended branches
    ga_releases = [b for b in recommended if b.startswith('release/')]
    development = [b for b in recommended if b in ['main', 'master', 'develop', 'development']]
    feature = [b for b in recommended if b.startswith('feature/')]
    hotfix = [b for b in recommended if b.startswith('hotfix/')]
    other = [b for b in recommended if b not in ga_releases + development + feature + hotfix]
    
    config_content = f"""# Auto-generated configuration from branch survey
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Estimated examples: {report.get('estimated_examples', 0)}

repository:
  path: "{report.get('repository', '/path/to/repo')}"
  name: "motadata"

branches:
  ga_releases:
{chr(10).join(f'    - "{b}"' for b in ga_releases) if ga_releases else '    []'}

  development:
{chr(10).join(f'    - "{b}"' for b in development) if development else '    []'}

  feature:
{chr(10).join(f'    - "{b}"' for b in feature) if feature else '    []'}

  hotfix:
{chr(10).join(f'    - "{b}"' for b in hotfix) if hotfix else '    []'}

  priority:
    ga_releases: 3
    development: 2
    hotfix: 2
    feature: 1

filters:
  include_commit_patterns:
    - "^[Ff]ix"
    - "^[Bb]ug"
    - "^[Pp]atch"
    - "^[Ff]eat"
    - "^[Aa]dd"
    - "^[Ii]mplement"
    - "^[Rr]efactor"
    - "^[Uu]pdate"
    - "^[Oo]ptimize"
    - "MOTADATA-[0-9]+"
    - "MOT-[0-9]+"
    
  exclude_commit_patterns:
    - "^[Ww]ip"
    - "^[Tt]emp"
    - "^[Mm]erge"
    - "^[Rr]evert"
    - "^[Bb]ump"
    - "^[Uu]pgrade"
    - "^[Ii]nitial"
    
  include_extensions:
    - ".java"
    - ".py"
    - ".yaml"
    - ".yml"
    - ".json"
    - ".xml"
    - ".properties"
    
  exclude_paths:
    - "node_modules/"
    - "__pycache__/"
    - "target/"
    - "build/"
    - "dist/"
    - ".git/"
    - "package-lock.json"
    - "yarn.lock"
    - ".min.js$"
    - ".min.css$"
    
  min_diff_lines: 2
  max_diff_lines: 100
  max_file_lines: 500
  max_hunks: 5

history:
  max_commits_per_branch: 2000
  since_date: null
  until_date: null
  deduplicate: true

output:
  format: "jsonl"
  file: "motadata_finetuning_data.jsonl"
  include_metadata: true
  system_prompt: |
    You are a senior Motadata engineer. Given a file and a task description,
    generate the precise unified diff to implement the change.
    Always use proper unified diff format with --- a/, +++ b/, and @@ headers.
"""
    
    with open(output_path, 'w') as f:
        f.write(config_content)


if __name__ == "__main__":
    main()
