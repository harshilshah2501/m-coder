#!/usr/bin/env python3
"""
Add reasoning/chain-of-thought to existing training examples.

This script helps create iteration 13 dataset by adding reasoning steps
before code generation, addressing Challenge #1 (immature output).

Usage:
    python add_reasoning.py --input v12_combined.jsonl --output v13_with_reasoning.jsonl --mode manual
    python add_reasoning.py --input v12_combined.jsonl --output v13_with_reasoning.jsonl --mode llm-assisted
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List
import sys

# Add OpenAI for LLM-assisted mode
try:
    from openai import OpenAI
except ImportError:
    print("Warning: openai not installed. LLM-assisted mode will not work.")
    print("Install with: pip install openai")


REASONING_TEMPLATE = """Let me analyze this task step-by-step:

**Understanding the Requirement**:
{requirement_analysis}

**Current State Analysis**:
{current_state}

**Implementation Plan**:
{implementation_steps}

**Considerations**:
{considerations}

**Code Changes**:
"""


def extract_task_from_user_message(user_content: str) -> Dict[str, str]:
    """Extract task description and file info from user message"""
    lines = user_content.split('\n')
    
    task = ""
    file_path = ""
    file_content = ""
    
    for i, line in enumerate(lines):
        if line.startswith("File:"):
            file_path = line.replace("File:", "").strip()
        elif line.startswith("Task:") or line.startswith("Description:"):
            task = line.split(":", 1)[1].strip()
        elif "Content:" in line or "```" in line:
            # Rest is file content
            file_content = '\n'.join(lines[i:])
            break
    
    return {
        "task": task,
        "file_path": file_path,
        "file_content": file_content
    }


def generate_reasoning_manual(example: Dict) -> str:
    """
    Interactive mode: Ask user to provide reasoning for this example.
    Returns reasoning text to insert before the diff.
    """
    messages = example.get("messages", [])
    
    # Find user message
    user_msg = next((m for m in messages if m["role"] == "user"), None)
    if not user_msg:
        return ""
    
    # Find assistant message (the diff)
    assistant_msg = next((m for m in messages if m["role"] == "assistant"), None)
    if not assistant_msg:
        return ""
    
    task_info = extract_task_from_user_message(user_msg["content"])
    
    print("\n" + "="*80)
    print("EXAMPLE TO ANNOTATE")
    print("="*80)
    print(f"Task: {task_info['task']}")
    print(f"File: {task_info['file_path']}")
    print("\nGenerated Diff (first 500 chars):")
    print(assistant_msg["content"][:500])
    print("...")
    print("\n" + "="*80)
    
    print("\nPlease provide reasoning for this change:")
    print("(Enter multi-line reasoning, type 'END' on a new line when done)")
    print("(Type 'SKIP' to skip this example)")
    print()
    
    reasoning_lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        if line.strip() == "SKIP":
            return None
        reasoning_lines.append(line)
    
    return '\n'.join(reasoning_lines)


def generate_reasoning_llm(example: Dict, client: OpenAI) -> str:
    """
    LLM-assisted mode: Use GPT-4 to generate reasoning, then ask user to validate.
    """
    messages = example.get("messages", [])
    
    user_msg = next((m for m in messages if m["role"] == "user"), None)
    assistant_msg = next((m for m in messages if m["role"] == "assistant"), None)
    
    if not user_msg or not assistant_msg:
        return ""
    
    task_info = extract_task_from_user_message(user_msg["content"])
    diff = assistant_msg["content"]
    
    # Ask GPT-4 to generate reasoning
    prompt = f"""You are a senior software engineer reviewing a code change.

Task: {task_info['task']}
File: {task_info['file_path']}

The following diff was generated to implement this task:

```diff
{diff[:2000]}  # Truncate for token limits
```

Please provide step-by-step reasoning that explains:
1. What the requirement is asking for
2. Analysis of the current code state
3. Implementation plan (what needs to change and why)
4. Important considerations (edge cases, performance, testing)

Format your response as clear, concise bullet points suitable for training an AI model.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior software engineer explaining code changes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        generated_reasoning = response.choices[0].message.content
        
        # Show to user for validation
        print("\n" + "="*80)
        print(f"Task: {task_info['task']}")
        print(f"File: {task_info['file_path']}")
        print("\nGPT-4 Generated Reasoning:")
        print("-"*80)
        print(generated_reasoning)
        print("-"*80)
        
        choice = input("\nAccept this reasoning? (y/n/edit/skip): ").strip().lower()
        
        if choice == 'y':
            return generated_reasoning
        elif choice == 'skip':
            return None
        elif choice == 'edit':
            print("Enter your edited version (type 'END' when done):")
            edited_lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                edited_lines.append(line)
            return '\n'.join(edited_lines)
        else:
            return None
            
    except Exception as e:
        print(f"Error generating reasoning with LLM: {e}")
        return None


def add_reasoning_to_example(example: Dict, reasoning: str) -> Dict:
    """
    Add reasoning to the assistant's response before the diff.
    """
    messages = example.get("messages", [])
    
    for msg in messages:
        if msg["role"] == "assistant":
            # Insert reasoning before the diff
            original_content = msg["content"]
            msg["content"] = f"{reasoning}\n\n{original_content}"
            break
    
    return example


def main():
    parser = argparse.ArgumentParser(description="Add reasoning to training examples")
    parser.add_argument("--input", required=True, help="Input JSONL file")
    parser.add_argument("--output", required=True, help="Output JSONL file")
    parser.add_argument("--mode", choices=["manual", "llm-assisted"], default="manual",
                       help="Mode: manual annotation or LLM-assisted")
    parser.add_argument("--limit", type=int, help="Limit number of examples to process")
    parser.add_argument("--openai-api-key", help="OpenAI API key for LLM-assisted mode")
    
    args = parser.parse_args()
    
    # Initialize OpenAI client if needed
    client = None
    if args.mode == "llm-assisted":
        if not args.openai_api_key:
            print("Error: --openai-api-key required for llm-assisted mode")
            sys.exit(1)
        client = OpenAI(api_key=args.openai_api_key)
    
    # Load input data
    print(f"Loading examples from {args.input}...")
    examples = []
    with open(args.input) as f:
        for line in f:
            examples.append(json.loads(line))
    
    print(f"Loaded {len(examples)} examples")
    
    if args.limit:
        examples = examples[:args.limit]
        print(f"Processing first {args.limit} examples")
    
    # Process examples
    output_examples = []
    skipped = 0
    
    for i, example in enumerate(examples):
        print(f"\n[{i+1}/{len(examples)}]")
        
        if args.mode == "manual":
            reasoning = generate_reasoning_manual(example)
        else:
            reasoning = generate_reasoning_llm(example, client)
        
        if reasoning is None:
            print("Skipped")
            skipped += 1
            continue
        
        # Add reasoning to example
        enhanced_example = add_reasoning_to_example(example.copy(), reasoning)
        output_examples.append(enhanced_example)
    
    # Save output
    print(f"\nSaving {len(output_examples)} enhanced examples to {args.output}...")
    with open(args.output, 'w') as f:
        for example in output_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"\nDone!")
    print(f"  Processed: {len(output_examples)}")
    print(f"  Skipped: {skipped}")
    print(f"  Output: {args.output}")


if __name__ == "__main__":
    main()

