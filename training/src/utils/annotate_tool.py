#!/usr/bin/env python3
"""
Interactive annotation tool with structured prompts.
Forces consistent format across all annotators.

Usage:
    python annotate_tool.py --input v12_combined.jsonl --output v13_annotated.jsonl --limit 50
"""

import json
import argparse
from pathlib import Path


def show_example(example: dict) -> None:
    """Display the example to annotate"""
    messages = example.get('messages', [])
    
    user_msg = next((m for m in messages if m['role'] == 'user'), None)
    assistant_msg = next((m for m in messages if m['role'] == 'assistant'), None)
    
    if not user_msg or not assistant_msg:
        print("⚠️  Warning: Example missing user or assistant message")
        return
    
    print("\n" + "="*80)
    print("TASK/PROMPT:")
    print("="*80)
    print(user_msg['content'][:300])
    if len(user_msg['content']) > 300:
        print("...")
    
    print("\n" + "="*80)
    print("GENERATED DIFF (first 500 chars):")
    print("="*80)
    print(assistant_msg['content'][:500])
    if len(assistant_msg['content']) > 500:
        print("...")
    print()


def annotate_example(example: dict) -> str:
    """Guide engineer through structured annotation"""
    
    show_example(example)
    
    print("="*80)
    print("ANNOTATION (be concise and specific)")
    print("="*80)
    print()
    
    # Check if user wants to skip
    skip = input("Skip this example? (y/N): ").strip().lower()
    if skip == 'y':
        return None
    
    # Forced structure
    print("\nAnswer these questions:")
    print()
    
    problem = input("1. What PROBLEM does this solve? (1-2 sentences): ").strip()
    if not problem:
        print("⚠️  Problem cannot be empty. Skipping.")
        return None
    
    print("\n2. What is the PLAN? (Enter 3-5 steps, one per line. Type 'END' when done):")
    plan_steps = []
    while True:
        step = input("   - ").strip()
        if step.upper() == 'END':
            break
        if step:
            plan_steps.append(step)
        if len(plan_steps) >= 5:
            print("   (Max 5 steps reached)")
            break
    
    if not plan_steps:
        print("⚠️  Plan cannot be empty. Skipping.")
        return None
    
    edge_cases = input("\n3. Any EDGE CASES or considerations? (comma-separated, or 'none'): ").strip()
    
    # Format as structured reasoning with XML tags
    reasoning = f"""<thinking>
**Problem**: {problem}
**Plan**:
{chr(10).join('- ' + step for step in plan_steps)}
**Edge Cases**: {edge_cases if edge_cases.lower() != 'none' else 'None identified'}
</thinking>"""
    
    # Show preview
    print("\n" + "="*80)
    print("PREVIEW:")
    print("="*80)
    print(reasoning)
    print()
    
    confirm = input("Accept this annotation? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("Discarded. Skipping example.")
        return None
    
    return reasoning


def add_reasoning_to_example(example: dict, reasoning: str) -> dict:
    """Add reasoning to the assistant's response"""
    messages = example.get('messages', [])
    
    for msg in messages:
        if msg['role'] == 'assistant':
            # Wrap original code in <code> tags and prepend reasoning
            original_content = msg['content']
            msg['content'] = f"{reasoning}\n\n<code>\n{original_content}\n</code>"
            break
    
    return example


def main():
    parser = argparse.ArgumentParser(description="Interactive annotation tool")
    parser.add_argument("--input", required=True, help="Input JSONL file")
    parser.add_argument("--output", required=True, help="Output JSONL file")
    parser.add_argument("--limit", type=int, default=50, help="Number of examples to annotate")
    parser.add_argument("--resume", action="store_true", help="Resume from existing output file")
    
    args = parser.parse_args()
    
    # Load input examples
    print(f"Loading examples from {args.input}...")
    examples = []
    with open(args.input) as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    
    print(f"Loaded {len(examples)} examples")
    
    # Check for existing output (resume mode)
    annotated = []
    start_index = 0
    
    if args.resume and Path(args.output).exists():
        print(f"Resuming from {args.output}...")
        with open(args.output) as f:
            for line in f:
                if line.strip():
                    annotated.append(json.loads(line))
        start_index = len(annotated)
        print(f"Already annotated: {start_index} examples")
    
    # Annotate examples
    print(f"\nAnnotating {args.limit} examples (starting from index {start_index})...")
    print("Tips:")
    print("  - Be concise but specific")
    print("  - Focus on WHY, not just WHAT")
    print("  - Think about edge cases")
    print("  - Type 'y' to skip examples that are unclear")
    print()
    
    target_count = min(args.limit, len(examples) - start_index)
    
    for i in range(start_index, start_index + target_count):
        if i >= len(examples):
            break
        
        print(f"\n{'='*80}")
        print(f"EXAMPLE {i+1}/{len(examples)} (Annotated: {len(annotated)}/{args.limit})")
        print(f"{'='*80}")
        
        reasoning = annotate_example(examples[i])
        
        if reasoning is None:
            print("⏭️  Skipped")
            continue
        
        # Add reasoning to example
        enhanced_example = add_reasoning_to_example(examples[i].copy(), reasoning)
        annotated.append(enhanced_example)
        
        # Save incrementally (crash-resistant)
        with open(args.output, 'w') as f:
            for ex in annotated:
                f.write(json.dumps(ex) + '\n')
        
        print(f"✅ Saved ({len(annotated)} total)")
        
        # Check if we've reached the limit
        if len(annotated) >= args.limit:
            break
    
    # Final summary
    print("\n" + "="*80)
    print("ANNOTATION COMPLETE")
    print("="*80)
    print(f"Total annotated: {len(annotated)}")
    print(f"Output file: {args.output}")
    print()
    print("Next steps:")
    print("  1. Review the annotated examples")
    print("  2. Combine with auto-generated examples")
    print("  3. Train iteration 13")


if __name__ == "__main__":
    main()

