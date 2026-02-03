#!/usr/bin/env python3
"""
Dataset Fix Script for V16.1
=============================
Fixes the critical issues identified in Dataset-analysis.md:

1. SCHEMA FIX: Convert all `qa_pair` format to `messages` format
2. PROMPT FIX: Change "unified diff" instructions to "SEARCH/REPLACE blocks"
3. Preserves metadata for traceability

Usage:
    python fix_dataset_v16_1.py

Output:
    datasets/v16_1_fixed/train.jsonl
    datasets/v16_1_fixed/val.jsonl
    datasets/v16_1_fixed/test.jsonl
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Paths
INPUT_DIR = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_splits")
OUTPUT_DIR = Path("/home/harshil/Harshil-PoCs/datasets/v16_1_fixed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# System prompt for code Q&A (for converted qa_pair entries)
QA_SYSTEM_PROMPT = """You are Motadata Coder, an expert on the Motadata codebase.
Answer questions about Motadata code accurately and concisely.
When explaining code, reference the specific class, method, and package."""

# Simple string replacements (no regex needed for most)
# Format: (old_string, new_string) - will be used with str.replace()
# Order matters - put longer/more specific strings first
SIMPLE_REPLACEMENTS = [
    # Fix the example code block in system prompts (this is the most important fix!)
    # The old format shows unified diff example, we replace it with SEARCH/REPLACE example
    # Note: After JSON loading, \n becomes actual newlines, so we use actual newlines here
    ('```diff\n--- a/path/to/file\n+++ b/path/to/file\n@@ ... @@\n- old\n+ new\n```',
     '```\nFile: path/to/file\n<<<< SEARCH\nold code\n====\nnew code\n>>>> REPLACE\n```'),

    # System prompt format instructions
    ('use unified diff format:', 'use SEARCH/REPLACE block format:'),
    ('When editing code, ALWAYS use unified diff format:', 'When editing code, ALWAYS use SEARCH/REPLACE block format:'),
    ('Always use proper unified diff format with --- a/, +++ b/, and @@ headers.',
     'Always use SEARCH/REPLACE blocks with <<<< SEARCH, ====, and >>>> REPLACE markers.'),
    ('Use proper unified diff format with --- a/ and +++ b/ headers',
     'Use SEARCH/REPLACE block format with <<<< SEARCH and >>>> REPLACE markers'),

    # Action instructions (with periods)
    ('use unified diff to implement the change.', 'use SEARCH/REPLACE blocks to implement the change.'),
    ('use unified diff to implement this change.', 'use SEARCH/REPLACE blocks to implement this change.'),
    ('use unified diffs to implement the change.', 'use SEARCH/REPLACE blocks to implement the change.'),
    ('use unified diffs to implement this change.', 'use SEARCH/REPLACE blocks to implement this change.'),

    # Action instructions (without periods - for mid-sentence usage)
    ('unified diffs for each file with proper format', 'SEARCH/REPLACE blocks for each file with proper format'),
    ('unified diffs for all files to implement this change', 'SEARCH/REPLACE blocks for all files to implement this change'),
    ('unified diff for all files to implement this change', 'SEARCH/REPLACE blocks for all files to implement this change'),
    ('unified diffs for each file', 'SEARCH/REPLACE blocks for each file'),
    ('unified diff for each file', 'SEARCH/REPLACE blocks for each file'),
    ('unified diff to implement the change', 'SEARCH/REPLACE blocks to implement the change'),
    ('unified diff to implement this change', 'SEARCH/REPLACE blocks to implement this change'),
    ('unified diff with proper format', 'SEARCH/REPLACE blocks with proper format'),
    ('unified diffs with proper format', 'SEARCH/REPLACE blocks with proper format'),
    ('unified diff format', 'SEARCH/REPLACE block format'),
    ('unified diffs', 'SEARCH/REPLACE blocks'),

    # Other instructions
    ('Generate diffs for ALL files', 'Generate SEARCH/REPLACE blocks for ALL files'),
    ('generate unified diff', 'generate SEARCH/REPLACE blocks'),
    ('Generate unified diff', 'Generate SEARCH/REPLACE blocks'),
]

# These are kept as regex for flexibility (not used currently but available)
OLD_PATTERNS = []


def convert_qa_pair_to_messages(entry: Dict) -> Dict:
    """Convert qa_pair format to messages format."""
    question = entry.get("question", "")
    answer = entry.get("answer", "")
    code = entry.get("code", "")
    source_file = entry.get("source_file", "")
    class_name = entry.get("class_name", "")
    method_name = entry.get("method_name", "")
    
    # Build context-rich user message
    user_content = question
    if code and code != "...":
        user_content += f"\n\nCode signature: {code}"
    if source_file:
        user_content += f"\nFile: {source_file}"
    
    # Build assistant response
    assistant_content = answer
    if class_name and method_name:
        # Add structured reference
        assistant_content = f"In `{class_name}.{method_name}()`:\n\n{answer}"
    
    return {
        "messages": [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content}
        ],
        "metadata": {
            "original_type": "qa_pair",
            "source_file": source_file,
            "class_name": class_name,
            "method_name": method_name,
            "package": entry.get("package", ""),
            "difficulty": entry.get("difficulty", ""),
            "tags": entry.get("tags", [])
        }
    }


def fix_content(content: str) -> str:
    """Replace unified diff instructions with SEARCH/REPLACE instructions in any content."""
    fixed = content

    # Apply simple string replacements
    for old_str, new_str in SIMPLE_REPLACEMENTS:
        fixed = fixed.replace(old_str, new_str)

    # Apply regex patterns if any
    for old_pattern, new_text in OLD_PATTERNS:
        fixed = re.sub(old_pattern, new_text, fixed, flags=re.IGNORECASE)

    return fixed


def process_messages_entry(entry: Dict) -> Dict:
    """Process a messages format entry - fix all messages."""
    messages = entry.get("messages", [])
    fixed_messages = []

    for msg in messages:
        fixed_msg = msg.copy()
        # Fix content for all roles (system, user, assistant)
        if msg.get("role") in ("system", "user", "assistant"):
            fixed_msg["content"] = fix_content(msg.get("content", ""))
        fixed_messages.append(fixed_msg)
    
    result = {"messages": fixed_messages}
    if "metadata" in entry:
        result["metadata"] = entry["metadata"]
    
    return result


def process_file(input_path: Path, output_path: Path) -> Dict[str, int]:
    """Process a single JSONL file and return stats."""
    stats = {"total": 0, "qa_pair_converted": 0, "messages_fixed": 0, "errors": 0}
    
    with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
        for line_num, line in enumerate(f_in, 1):
            if not line.strip():
                continue
            
            try:
                entry = json.loads(line)
                stats["total"] += 1
                
                if entry.get("type") == "qa_pair":
                    # Convert qa_pair to messages
                    fixed = convert_qa_pair_to_messages(entry)
                    stats["qa_pair_converted"] += 1
                elif "messages" in entry:
                    # Fix system prompts in messages
                    fixed = process_messages_entry(entry)
                    stats["messages_fixed"] += 1
                else:
                    # Unknown format - keep as is
                    fixed = entry
                
                f_out.write(json.dumps(fixed, ensure_ascii=False) + "\n")
                
            except json.JSONDecodeError as e:
                print(f"  ⚠️ Line {line_num}: JSON error - {e}")
                stats["errors"] += 1
            except Exception as e:
                print(f"  ⚠️ Line {line_num}: Error - {e}")
                stats["errors"] += 1
    
    return stats


def main():
    """Main entry point."""
    print("=" * 80)
    print("V16.1 DATASET FIX SCRIPT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Input:  {INPUT_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 80)

    files = ["train.jsonl", "val.jsonl", "test.jsonl"]
    total_stats = {"total": 0, "qa_pair_converted": 0, "messages_fixed": 0, "errors": 0}

    for filename in files:
        input_path = INPUT_DIR / filename
        output_path = OUTPUT_DIR / filename

        if not input_path.exists():
            print(f"\n⚠️ Skipping {filename} - not found")
            continue

        print(f"\n📄 Processing {filename}...")
        stats = process_file(input_path, output_path)

        print(f"   ✓ Total entries: {stats['total']}")
        print(f"   ✓ qa_pair → messages: {stats['qa_pair_converted']}")
        print(f"   ✓ System prompts fixed: {stats['messages_fixed']}")
        if stats['errors'] > 0:
            print(f"   ⚠️ Errors: {stats['errors']}")

        for key in total_stats:
            total_stats[key] += stats[key]

    # Write summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "input_dir": str(INPUT_DIR),
        "output_dir": str(OUTPUT_DIR),
        "stats": total_stats,
        "fixes_applied": [
            "Converted qa_pair format to messages format",
            "Changed 'unified diff' instructions to 'SEARCH/REPLACE blocks'"
        ]
    }

    summary_path = OUTPUT_DIR / "fix_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total entries processed: {total_stats['total']}")
    print(f"qa_pair → messages:      {total_stats['qa_pair_converted']}")
    print(f"System prompts fixed:    {total_stats['messages_fixed']}")
    print(f"Errors:                  {total_stats['errors']}")
    print(f"\nOutput saved to: {OUTPUT_DIR}")
    print(f"Summary saved to: {summary_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()

