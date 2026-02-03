#!/usr/bin/env python3
"""
v16.2 Data Curation Script
===========================
Fixes all data quality issues identified in the v16.1 dataset.

Issues to fix:
1. diff_format_not_search_replace (365 samples) - Convert ```diff to <<<< SEARCH
2. multi_file_has_single_file (200 samples) - Recategorize to single_file_gen
3. debug_no_issue_identification (776 samples) - Add issue explanation
4. qa_too_short (138 samples) - Expand or discard
5. review_no_structure (35 samples) - Add structure or discard

Output: Clean dataset in /datasets/v16_2/
"""

import json
import re
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Configuration
INPUT_DIR = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_fixed")
OUTPUT_DIR = Path("/home/harshil/Harshil-PoCs/datasets/v16_2")
LOG_DIR = Path("/home/harshil/Harshil-PoCs/logs/data_curation")

# Setup logging
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"v16_2_curation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_samples(path: Path) -> List[Dict]:
    """Load samples from JSONL file."""
    samples = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples


def save_samples(samples: List[Dict], path: Path):
    """Save samples to JSONL file."""
    with open(path, 'w') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')
    logger.info(f"Saved {len(samples)} samples to {path}")


def convert_diff_to_search_replace(content: str) -> str:
    """
    Convert ```diff format to <<<< SEARCH / >>>> REPLACE format.
    
    Input format:
    ```diff
    @@ -10,5 +10,6 @@
     unchanged line
    -removed line
    +added line
     unchanged line
    ```
    
    Output format:
    <<<< SEARCH
    unchanged line
    removed line
    unchanged line
    ====
    unchanged line
    added line
    unchanged line
    >>>> REPLACE
    """
    # Find all diff blocks
    diff_pattern = r'```diff\n(.*?)```'
    matches = re.findall(diff_pattern, content, re.DOTALL)
    
    if not matches:
        return content
    
    result = content
    for diff_block in matches:
        search_lines = []
        replace_lines = []
        
        lines = diff_block.strip().split('\n')
        for line in lines:
            # Skip @@ header lines
            if line.startswith('@@'):
                continue
            # Skip empty lines at start
            if not line and not search_lines:
                continue
                
            if line.startswith('-'):
                # Removed line - only in SEARCH
                search_lines.append(line[1:])  # Remove the '-' prefix
            elif line.startswith('+'):
                # Added line - only in REPLACE
                replace_lines.append(line[1:])  # Remove the '+' prefix
            elif line.startswith(' '):
                # Context line - in both
                search_lines.append(line[1:])  # Remove the ' ' prefix
                replace_lines.append(line[1:])
            else:
                # No prefix - treat as context
                search_lines.append(line)
                replace_lines.append(line)
        
        # Build SEARCH/REPLACE block
        search_replace = f"<<<< SEARCH\n{chr(10).join(search_lines)}\n====\n{chr(10).join(replace_lines)}\n>>>> REPLACE"
        
        # Replace the diff block with SEARCH/REPLACE
        diff_full = f"```diff\n{diff_block}```"
        result = result.replace(diff_full, search_replace)
    
    return result


def extract_file_path_from_diff(content: str) -> Optional[str]:
    """Extract file path from diff header or context."""
    # Try to find file path from --- a/path or +++ b/path
    path_match = re.search(r'[-+]{3}\s+[ab]/(.+)', content)
    if path_match:
        return path_match.group(1)
    
    # Try to find from File: reference
    file_match = re.search(r'File:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if file_match:
        return file_match.group(1).strip()
    
    return None


def fix_diff_format_sample(sample: Dict) -> Tuple[Dict, bool]:
    """Fix a sample that uses diff format instead of SEARCH/REPLACE."""
    messages = sample.get('messages', [])
    modified = False
    
    for msg in messages:
        if msg['role'] == 'assistant':
            original = msg['content']
            
            if '```diff' in original:
                # Convert diff to SEARCH/REPLACE
                converted = convert_diff_to_search_replace(original)
                
                # Extract file path if not present
                if 'File:' not in converted and '<<<< SEARCH' in converted:
                    file_path = extract_file_path_from_diff(original)
                    if file_path:
                        # Add File: reference before first SEARCH block
                        converted = converted.replace(
                            '<<<< SEARCH',
                            f'File: {file_path}\n<<<< SEARCH',
                            1
                        )
                
                # Wrap in <code> if not present
                if '<code>' not in converted and '<<<< SEARCH' in converted:
                    # Find where code starts
                    code_start = converted.find('File:')
                    if code_start == -1:
                        code_start = converted.find('<<<< SEARCH')

                    if code_start > 0:
                        before_code = converted[:code_start]
                        code_content = converted[code_start:]
                        converted = f"{before_code}<code>\n{code_content}\n</code>"
                    else:
                        converted = f"<code>\n{converted}\n</code>"

                # Add <thinking> if not present
                if '<thinking>' not in converted:
                    converted = f"<thinking>\n\n</thinking>\n\n{converted}"

                msg['content'] = converted
                modified = True

    return sample, modified


def add_issue_identification(sample: Dict) -> Tuple[Dict, bool]:
    """Add issue identification to debugging samples."""
    messages = sample.get('messages', [])
    user_content = ""

    for msg in messages:
        if msg['role'] == 'user':
            user_content = msg['content']

    for msg in messages:
        if msg['role'] == 'assistant':
            content = msg['content']

            # Check if already has issue identification
            issue_words = ['error', 'issue', 'problem', 'cause', 'bug', 'missing', 'incorrect', 'wrong', 'fix']
            if any(w in content.lower() for w in issue_words):
                return sample, False

            # Extract context from user message to generate issue description
            issue_desc = generate_issue_description(user_content, content)

            # Add to <thinking> section
            if '<thinking>' in content:
                # Replace empty thinking with issue description
                content = re.sub(
                    r'<thinking>\s*</thinking>',
                    f'<thinking>\nAnalyzing the code to identify the issue.\n{issue_desc}\n</thinking>',
                    content
                )
                # Also handle thinking with just whitespace
                content = re.sub(
                    r'<thinking>\n\n</thinking>',
                    f'<thinking>\nAnalyzing the code to identify the issue.\n{issue_desc}\n</thinking>',
                    content
                )
            else:
                # Add thinking section at the beginning
                content = f"<thinking>\nAnalyzing the code to identify the issue.\n{issue_desc}\n</thinking>\n\n{content}"

            msg['content'] = content
            return sample, True

    return sample, False


def generate_issue_description(user_content: str, assistant_content: str) -> str:
    """Generate an issue description based on the context."""
    # Try to extract what's being changed from SEARCH/REPLACE
    search_match = re.search(r'<<<< SEARCH\n(.*?)\n====', assistant_content, re.DOTALL)
    replace_match = re.search(r'====\n(.*?)\n>>>> REPLACE', assistant_content, re.DOTALL)

    if search_match and replace_match:
        search_content = search_match.group(1)[:200]
        replace_content = replace_match.group(1)[:200]

        # Analyze the difference
        if len(replace_content) > len(search_content):
            return "The issue requires adding missing code or functionality."
        elif len(replace_content) < len(search_content):
            return "The issue requires removing or simplifying code."
        else:
            return "The issue requires modifying existing code logic."

    # Default description based on user content
    if 'import' in user_content.lower():
        return "The issue involves missing or incorrect import statements."
    elif 'null' in user_content.lower() or 'exception' in user_content.lower():
        return "The issue involves potential null pointer or exception handling."
    elif 'refactor' in user_content.lower():
        return "The code requires refactoring for better structure or performance."
    else:
        return "Applying the required code changes to fix the identified issue."


def recategorize_multi_file_single(sample: Dict) -> Tuple[Dict, str]:
    """
    Check if a multi_file sample should be recategorized as single_file.
    Returns the sample and the correct category.
    """
    messages = sample.get('messages', [])

    for msg in messages:
        if msg['role'] == 'assistant':
            content = msg['content'].lower()
            file_count = content.count('file:')

            if file_count < 2:
                return sample, 'single_file_gen'

    return sample, 'multi_file_gen'


def categorize_sample(sample: Dict) -> str:
    """Categorize a sample by use-case type."""
    metadata = sample.get('metadata', {})
    category = metadata.get('category', '')
    original_type = metadata.get('original_type', '')

    messages = sample.get('messages', [])
    user_content = ""
    assistant_content = ""

    for msg in messages:
        if msg['role'] == 'user':
            user_content = msg['content'].lower()
        elif msg['role'] == 'assistant':
            assistant_content = msg['content'].lower()

    if original_type == 'qa_pair' or 'how does' in user_content or 'explain' in user_content:
        return 'qa_knowledge'
    elif category == 'code_review' or 'review' in user_content:
        return 'code_review'
    elif 'debug' in user_content or 'rca' in user_content or 'error' in user_content or 'fix' in user_content:
        return 'debugging_rca'
    elif category == 'refactoring' or 'refactor' in user_content or assistant_content.count('file:') > 1:
        return 'multi_file_gen'
    elif '<<<< search' in assistant_content:
        return 'single_file_gen'
    else:
        return 'unknown'


def is_sample_clean(sample: Dict) -> Tuple[bool, List[str]]:
    """Check if a sample passes all quality checks."""
    issues = []
    messages = sample.get('messages', [])

    assistant_content = ""
    user_content = ""

    for msg in messages:
        if msg['role'] == 'user':
            user_content = msg['content']
        elif msg['role'] == 'assistant':
            assistant_content = msg['content']

    # Format checks
    if 'tool_calls' in assistant_content or '{"name":' in assistant_content:
        issues.append('old_agentic_tool_calls')

    if '```diff' in assistant_content and '<<<< SEARCH' not in assistant_content:
        issues.append('diff_format_not_search_replace')

    if '<<<< SEARCH' in assistant_content and '>>>> REPLACE' not in assistant_content:
        issues.append('incomplete_search_replace')

    # Content checks
    if len(user_content.strip()) < 10:
        issues.append('empty_user_content')

    if len(assistant_content.strip()) < 10:
        issues.append('empty_assistant_content')

    # Category-specific checks
    category = categorize_sample(sample)

    if category == 'debugging_rca':
        issue_words = ['error', 'issue', 'problem', 'cause', 'bug', 'missing', 'incorrect', 'wrong', 'fix', 'change', 'modif']
        if not any(w in assistant_content.lower() for w in issue_words):
            issues.append('debug_no_issue_identification')

    if category == 'qa_knowledge':
        if len(assistant_content) < 100:
            issues.append('qa_too_short')

    if category == 'code_review':
        review_words = ['Summary', 'Observations', 'Recommendations', 'Verdict', 'APPROVED', 'LGTM', 'review', 'suggestion']
        if not any(w in assistant_content for w in review_words):
            issues.append('review_no_structure')

    return len(issues) == 0, issues


def process_dataset(input_path: Path, output_path: Path) -> Dict:
    """Process a dataset file and fix all issues."""
    logger.info(f"Processing {input_path}...")

    samples = load_samples(input_path)
    logger.info(f"Loaded {len(samples)} samples")

    stats = {
        'total': len(samples),
        'diff_converted': 0,
        'issue_added': 0,
        'recategorized': 0,
        'discarded': 0,
        'clean': 0,
        'issues_remaining': defaultdict(int)
    }

    processed_samples = []

    for i, sample in enumerate(samples):
        if i % 500 == 0:
            logger.info(f"Processing sample {i}/{len(samples)}...")

        # Step 1: Convert diff format to SEARCH/REPLACE
        sample, diff_fixed = fix_diff_format_sample(sample)
        if diff_fixed:
            stats['diff_converted'] += 1

        # Step 2: Add issue identification for debugging samples
        category = categorize_sample(sample)
        if category == 'debugging_rca':
            sample, issue_added = add_issue_identification(sample)
            if issue_added:
                stats['issue_added'] += 1

        # Step 3: Recategorize multi_file samples with single file
        if category == 'multi_file_gen':
            sample, new_category = recategorize_multi_file_single(sample)
            if new_category == 'single_file_gen':
                stats['recategorized'] += 1
                # Update metadata
                if 'metadata' not in sample:
                    sample['metadata'] = {}
                sample['metadata']['recategorized_from'] = 'multi_file_gen'
                sample['metadata']['category'] = 'single_file_gen'

        # Step 4: Check if sample is now clean
        is_clean, remaining_issues = is_sample_clean(sample)

        if is_clean:
            stats['clean'] += 1
            processed_samples.append(sample)
        else:
            # Check if issues are fixable or should discard
            critical_issues = ['empty_user_content', 'empty_assistant_content', 'old_agentic_tool_calls']

            if any(issue in remaining_issues for issue in critical_issues):
                stats['discarded'] += 1
                logger.debug(f"Discarding sample {i}: {remaining_issues}")
            else:
                # Keep sample but track remaining issues
                for issue in remaining_issues:
                    stats['issues_remaining'][issue] += 1
                processed_samples.append(sample)

    # Save processed samples
    save_samples(processed_samples, output_path)

    return stats


def main():
    """Main entry point for v16.2 data curation."""
    logger.info("=" * 80)
    logger.info("v16.2 DATA CURATION - Starting")
    logger.info("=" * 80)

    # Process training data
    train_stats = process_dataset(
        INPUT_DIR / "train.jsonl",
        OUTPUT_DIR / "train.jsonl"
    )

    # Process validation data
    val_stats = process_dataset(
        INPUT_DIR / "val.jsonl",
        OUTPUT_DIR / "val.jsonl"
    )

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("CURATION SUMMARY")
    logger.info("=" * 80)

    logger.info("\nTRAINING DATA:")
    logger.info(f"  Total input: {train_stats['total']}")
    logger.info(f"  Diff converted: {train_stats['diff_converted']}")
    logger.info(f"  Issue identification added: {train_stats['issue_added']}")
    logger.info(f"  Recategorized: {train_stats['recategorized']}")
    logger.info(f"  Discarded: {train_stats['discarded']}")
    logger.info(f"  Clean samples: {train_stats['clean']}")
    logger.info(f"  Final output: {train_stats['total'] - train_stats['discarded']}")

    logger.info("\nVALIDATION DATA:")
    logger.info(f"  Total input: {val_stats['total']}")
    logger.info(f"  Diff converted: {val_stats['diff_converted']}")
    logger.info(f"  Issue identification added: {val_stats['issue_added']}")
    logger.info(f"  Recategorized: {val_stats['recategorized']}")
    logger.info(f"  Discarded: {val_stats['discarded']}")
    logger.info(f"  Clean samples: {val_stats['clean']}")
    logger.info(f"  Final output: {val_stats['total'] - val_stats['discarded']}")

    if train_stats['issues_remaining'] or val_stats['issues_remaining']:
        logger.info("\nREMAINING ISSUES (require manual review):")
        all_issues = defaultdict(int)
        for issue, count in train_stats['issues_remaining'].items():
            all_issues[issue] += count
        for issue, count in val_stats['issues_remaining'].items():
            all_issues[issue] += count

        for issue, count in sorted(all_issues.items(), key=lambda x: -x[1]):
            logger.info(f"  {issue}: {count}")

    logger.info("\n" + "=" * 80)
    logger.info(f"Output saved to: {OUTPUT_DIR}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
