#!/usr/bin/env python3
"""
Automated quality judging for generated code using GPT-4o/Claude.

This creates a self-improving data flywheel:
v12 → generate → judge → filter → v13 dataset

Usage:
    python auto_judge.py --input generated_examples.jsonl --output high_quality.jsonl --threshold 12
"""

import json
import argparse
from openai import OpenAI
from typing import Dict, List


JUDGE_PROMPT_TEMPLATE = """You are a senior code reviewer at Motadata.

JIRA Ticket/Task:
{task}

Generated Code:
{code}

Evaluate this code on three criteria (0-5 scale each):

1. **Correctness** (0-5): Does it solve the stated task/ticket?
   - 5: Perfect solution
   - 3-4: Mostly correct, minor issues
   - 1-2: Partially correct
   - 0: Wrong or doesn't address task

2. **Completeness** (0-5): Is the diff complete and not truncated?
   - 5: Complete, balanced braces/hunks, proper ending
   - 3-4: Mostly complete, minor formatting issues
   - 1-2: Incomplete or truncated
   - 0: Severely truncated or malformed

3. **Quality** (0-5): Is it clean, maintainable, follows best practices?
   - 5: Production-ready, excellent code
   - 3-4: Good code, minor improvements possible
   - 1-2: Works but has quality issues
   - 0: Poor quality, major issues

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "correctness": <0-5>,
  "completeness": <0-5>,
  "quality": <0-5>,
  "total": <sum of above>,
  "reasoning": "<brief 1-2 sentence explanation>",
  "accept": <true if total >= 12, false otherwise>
}}
"""


def extract_task_and_code(example: Dict) -> tuple:
    """Extract task description and generated code from example"""
    messages = example.get('messages', [])
    
    user_msg = next((m for m in messages if m['role'] == 'user'), None)
    assistant_msg = next((m for m in messages if m['role'] == 'assistant'), None)
    
    if not user_msg or not assistant_msg:
        return None, None
    
    task = user_msg['content']
    code = assistant_msg['content']
    
    return task, code


def judge_example(task: str, code: str, client: OpenAI, model: str = "gpt-4o") -> Dict:
    """Score a generated code example using LLM judge"""
    
    prompt = JUDGE_PROMPT_TEMPLATE.format(task=task[:1000], code=code[:2000])
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate structure
        required_keys = ['correctness', 'completeness', 'quality', 'total', 'reasoning', 'accept']
        if not all(k in result for k in required_keys):
            return {
                "error": "Invalid response structure",
                "raw_response": response.choices[0].message.content
            }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e)
        }


def auto_curate(input_file: str, output_file: str, threshold: int = 12, 
                api_key: str = None, model: str = "gpt-4o"):
    """Filter examples using automated judge"""
    
    client = OpenAI(api_key=api_key) if api_key else OpenAI()
    
    print(f"Loading examples from {input_file}...")
    examples = []
    with open(input_file) as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    
    print(f"Loaded {len(examples)} examples")
    print(f"Threshold: {threshold}/15")
    print(f"Model: {model}")
    print()
    
    accepted = []
    rejected = []
    errors = []
    
    for i, ex in enumerate(examples):
        print(f"[{i+1}/{len(examples)}] Judging...", end=" ")
        
        task, code = extract_task_and_code(ex)
        
        if not task or not code:
            print("❌ Skipped (invalid format)")
            errors.append((ex, "Invalid format"))
            continue
        
        score = judge_example(task, code, client, model)
        
        if 'error' in score:
            print(f"❌ Error: {score['error']}")
            errors.append((ex, score))
            continue
        
        total = score['total']
        
        if total >= threshold:
            print(f"✅ Accept (score: {total}/15)")
            accepted.append(ex)
        else:
            print(f"❌ Reject (score: {total}/15) - {score['reasoning'][:50]}")
            rejected.append((ex, score))
        
        # Save incrementally
        if len(accepted) % 10 == 0:
            with open(output_file, 'w') as f:
                for a in accepted:
                    f.write(json.dumps(a) + '\n')
    
    # Final save
    with open(output_file, 'w') as f:
        for ex in accepted:
            f.write(json.dumps(ex) + '\n')
    
    # Save rejected for review
    rejected_file = output_file.replace('.jsonl', '_rejected.jsonl')
    with open(rejected_file, 'w') as f:
        for ex, score in rejected:
            f.write(json.dumps({"example": ex, "score": score}) + '\n')
    
    # Summary
    print("\n" + "="*80)
    print("CURATION COMPLETE")
    print("="*80)
    print(f"Total examples: {len(examples)}")
    print(f"Accepted: {len(accepted)} ({len(accepted)/len(examples)*100:.1f}%)")
    print(f"Rejected: {len(rejected)} ({len(rejected)/len(examples)*100:.1f}%)")
    print(f"Errors: {len(errors)}")
    print()
    print(f"Accepted examples saved to: {output_file}")
    print(f"Rejected examples saved to: {rejected_file}")
    
    # Score distribution
    if rejected:
        avg_rejected_score = sum(s['total'] for _, s in rejected if 'total' in s) / len(rejected)
        print(f"\nAverage rejected score: {avg_rejected_score:.1f}/15")
    
    return accepted, rejected, errors


def main():
    parser = argparse.ArgumentParser(description="Automated code quality judging")
    parser.add_argument("--input", required=True, help="Input JSONL file with examples")
    parser.add_argument("--output", required=True, help="Output JSONL file for accepted examples")
    parser.add_argument("--threshold", type=int, default=12, help="Minimum score to accept (0-15)")
    parser.add_argument("--model", default="gpt-4o", help="Judge model (gpt-4o, gpt-4, claude-3-5-sonnet)")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    
    args = parser.parse_args()
    
    auto_curate(args.input, args.output, args.threshold, args.api_key, args.model)


if __name__ == "__main__":
    main()

