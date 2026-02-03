#!/usr/bin/env python3
"""
KPI 2: Output Truncation Prevention Test
=========================================
Purpose: Test 100 validation samples for truncation, bracket matching, and token budget.

Target: ≥99% complete responses (≤1 truncation per 100)

This script:
1. Loads 100 samples from validation set
2. Runs inference on merged model
3. Checks for truncation markers
4. Validates bracket/quote matching
5. Verifies token budget <95%
6. Generates detailed report
"""

import json
import torch
import time
import re
from pathlib import Path
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
from collections import defaultdict

# CONFIGURATION
MERGED_MODEL_PATH = "/home/harshil/Harshil-PoCs/models/v16_1_merged"
DATASET_DIR = "/home/harshil/Harshil-PoCs/datasets/v16_1_fixed"
NUM_SAMPLES = 100
MAX_NEW_TOKENS = 512
OUTPUT_DIR = "/home/harshil/Harshil-PoCs/evaluation/results"


def load_validation_samples(num_samples=100):
    """Load samples from validation set."""
    print(f"\n📂 Loading {num_samples} validation samples...")
    
    val_path = Path(DATASET_DIR) / "val.jsonl"
    samples = []
    
    with open(val_path, 'r') as f:
        for i, line in enumerate(f):
            if i >= num_samples:
                break
            if line.strip():
                samples.append(json.loads(line))
    
    print(f"   ✓ Loaded {len(samples)} samples")
    return samples


def format_prompt(messages, tokenizer):
    """Format messages using chat template - EXCLUDE assistant response."""
    # Only include system and user messages, not the expected assistant response
    prompt_messages = [m for m in messages if m['role'] != 'assistant']
    return tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True
    )


def check_truncation(response):
    """Check for truncation markers."""
    truncation_markers = ['...', '(truncated)', '<truncated>', '[...]', '…']
    last_100 = response[-100:] if len(response) > 100 else response
    
    for marker in truncation_markers:
        if marker in last_100:
            return True, marker
    return False, None


def check_bracket_matching(response):
    """Check if brackets and quotes are matched."""
    checks = {
        'curly_braces': response.count('{') == response.count('}'),
        'square_brackets': response.count('[') == response.count(']'),
        'parentheses': response.count('(') == response.count(')'),
        'double_quotes': response.count('"') % 2 == 0,
        'single_quotes': response.count("'") % 2 == 0
    }
    return checks, all(checks.values())


def check_diff_completeness(response):
    """Check if diff has required headers (for SEARCH/REPLACE tasks)."""
    has_search = '<<<< SEARCH' in response or '--- a/' in response
    has_replace = '>>>> REPLACE' in response or '+++ b/' in response
    
    if has_search or has_replace:
        return {
            'is_diff': True,
            'has_search_marker': has_search,
            'has_replace_marker': has_replace,
            'complete': has_search and has_replace
        }
    return {'is_diff': False, 'complete': True}


def run_kpi2_evaluation(model, tokenizer, samples):
    """Run KPI 2 evaluation on all samples."""
    print(f"\n🧪 Running KPI 2 Evaluation on {len(samples)} samples...")
    print("=" * 80)
    
    results = []
    stats = {
        'total': len(samples),
        'truncated': 0,
        'bracket_mismatches': 0,
        'incomplete_diffs': 0,
        'token_budget_exceeded': 0,
        'complete_responses': 0
    }
    
    for i, sample in enumerate(samples):
        prompt = format_prompt(sample['messages'], tokenizer)

        # Tokenize and measure
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        input_token_count = inputs['input_ids'].shape[1]
        
        # Generate
        start_time = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        inference_time = time.time() - start_time
        
        # Decode
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        output_token_count = outputs[0].shape[0]
        generated_tokens = output_token_count - input_token_count
        
        # Run checks
        is_truncated, truncation_marker = check_truncation(response)
        bracket_checks, brackets_matched = check_bracket_matching(response)
        diff_check = check_diff_completeness(response)
        token_budget_pct = (generated_tokens / MAX_NEW_TOKENS) * 100
        
        # Update stats
        if is_truncated:
            stats['truncated'] += 1
        if not brackets_matched:
            stats['bracket_mismatches'] += 1
        if diff_check['is_diff'] and not diff_check['complete']:
            stats['incomplete_diffs'] += 1
        if token_budget_pct >= 95:
            stats['token_budget_exceeded'] += 1
        if not is_truncated and brackets_matched and diff_check['complete'] and token_budget_pct < 95:
            stats['complete_responses'] += 1
        
        # Store result
        result = {
            'sample_id': i,
            'prompt_length': len(prompt),
            'response_length': len(response),
            'input_tokens': input_token_count,
            'generated_tokens': generated_tokens,
            'token_budget_pct': round(token_budget_pct, 2),
            'inference_time': round(inference_time, 2),
            'is_truncated': is_truncated,
            'truncation_marker': truncation_marker,
            'brackets_matched': brackets_matched,
            'bracket_checks': bracket_checks,
            'diff_check': diff_check,
            'passed_all_checks': not is_truncated and brackets_matched and diff_check['complete'] and token_budget_pct < 95
        }
        results.append(result)
        
        # Progress
        if (i + 1) % 10 == 0:
            print(f"   Processed {i+1}/{len(samples)} samples...")
    
    print("\n" + "=" * 80)
    return results, stats


def generate_report(results, stats):
    """Generate KPI 2 evaluation report."""
    completion_rate = (stats['complete_responses'] / stats['total']) * 100
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'kpi': 'KPI 2: Output Truncation Prevention',
        'target': '≥99% complete responses',
        'samples_tested': stats['total'],
        'summary': {
            'completion_rate': round(completion_rate, 2),
            'truncated_count': stats['truncated'],
            'bracket_mismatch_count': stats['bracket_mismatches'],
            'incomplete_diff_count': stats['incomplete_diffs'],
            'token_budget_exceeded_count': stats['token_budget_exceeded'],
            'complete_responses': stats['complete_responses']
        },
        'pass_fail': {
            'target_met': completion_rate >= 99.0,
            'status': 'PASS' if completion_rate >= 99.0 else 'FAIL',
            'gap': round(99.0 - completion_rate, 2) if completion_rate < 99.0 else 0
        },
        'detailed_results': results
    }
    
    return report


def main():
    print("=" * 80)
    print("KPI 2: OUTPUT TRUNCATION PREVENTION TEST")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Model: {MERGED_MODEL_PATH}")
    print(f"Samples: {NUM_SAMPLES}")
    print(f"Max Tokens: {MAX_NEW_TOKENS}")
    print("=" * 80)
    
    # Load samples
    samples = load_validation_samples(NUM_SAMPLES)
    
    # Load model
    print("\n🔧 Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(MERGED_MODEL_PATH)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        MERGED_MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    print("   ✓ Model loaded")
    
    # Run evaluation
    results, stats = run_kpi2_evaluation(model, tokenizer, samples)
    
    # Generate report
    report = generate_report(results, stats)
    
    # Save report
    output_path = Path(OUTPUT_DIR) / f"kpi2_truncation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("KPI 2 EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Completion Rate: {report['summary']['completion_rate']}%")
    print(f"Target: ≥99%")
    print(f"Status: {report['pass_fail']['status']}")
    print(f"\nTruncated: {stats['truncated']}/{stats['total']}")
    print(f"Bracket Mismatches: {stats['bracket_mismatches']}/{stats['total']}")
    print(f"Incomplete Diffs: {stats['incomplete_diffs']}/{stats['total']}")
    print(f"Token Budget Exceeded: {stats['token_budget_exceeded']}/{stats['total']}")
    print(f"\n✅ Complete Responses: {stats['complete_responses']}/{stats['total']}")
    print(f"\n📄 Report saved: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()

