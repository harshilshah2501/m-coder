#!/usr/bin/env python3
"""
KPI 3: System Prompt & Dataset Coverage Test
=============================================
Purpose: Test 100 samples across 5 use-cases to validate coverage.

Target: 100% of use-cases pass (all 5)

Use-Cases:
1. Q&A / Knowledge (20 samples)
2. Code Gen - Single File (20 samples)
3. Code Gen - Multi-File (20 samples)
4. Debugging / RCA (20 samples)
5. Code Review (20 samples)

This script:
1. Categorizes validation samples by use-case
2. Runs inference on 20 samples per use-case
3. Validates expected behavior for each use-case
4. Calculates pass rate per use-case
5. Generates detailed report
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
SAMPLES_PER_USE_CASE = 20
MAX_NEW_TOKENS = 512
OUTPUT_DIR = "/home/harshil/Harshil-PoCs/evaluation/results"


def categorize_sample(sample):
    """Categorize sample by use-case based on metadata and content."""
    metadata = sample.get('metadata', {})
    category = metadata.get('category', '')
    original_type = metadata.get('original_type', '')
    
    # Check messages for patterns
    messages = sample.get('messages', [])
    user_content = ""
    assistant_content = ""
    
    for msg in messages:
        if msg['role'] == 'user':
            user_content = msg['content'].lower()
        elif msg['role'] == 'assistant':
            assistant_content = msg['content'].lower()
    
    # Categorization logic
    if original_type == 'qa_pair' or 'how does' in user_content or 'explain' in user_content:
        return 'qa_knowledge'
    elif category == 'code_review' or 'review' in user_content:
        return 'code_review'
    elif category == 'refactoring' or 'refactor' in user_content:
        return 'multi_file_gen'
    elif category == 'single_file' or (category == 'code_edits' and 'file:' in user_content.lower()):
        return 'single_file_gen'
    elif 'debug' in user_content or 'rca' in user_content or 'error' in user_content:
        return 'debugging_rca'
    elif '<<<< search' in assistant_content or 'search/replace' in user_content:
        # Check if multi-file
        if assistant_content.count('file:') > 1 or 'files to' in user_content:
            return 'multi_file_gen'
        else:
            return 'single_file_gen'
    else:
        return 'unknown'


def load_categorized_samples(samples_per_category=20):
    """Load and categorize validation samples."""
    print(f"\n📂 Loading and categorizing validation samples...")
    
    val_path = Path(DATASET_DIR) / "val.jsonl"
    categorized = defaultdict(list)
    
    with open(val_path, 'r') as f:
        for line in f:
            if line.strip():
                sample = json.loads(line)
                category = categorize_sample(sample)
                categorized[category].append(sample)
    
    # Select samples per category
    selected = {}
    use_cases = ['qa_knowledge', 'single_file_gen', 'multi_file_gen', 'debugging_rca', 'code_review']
    
    for use_case in use_cases:
        available = categorized.get(use_case, [])
        selected[use_case] = available[:samples_per_category]
        print(f"   {use_case}: {len(selected[use_case])} samples (available: {len(available)})")
    
    return selected


def format_prompt(messages, tokenizer):
    """Format messages using chat template - EXCLUDE assistant response."""
    # Only include system and user messages, not the expected assistant response
    prompt_messages = [m for m in messages if m['role'] != 'assistant']
    return tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True
    )


def validate_qa_knowledge(response):
    """Validate Q&A response: should explain with code citations."""
    checks = {
        'has_explanation': len(response) > 100,
        'has_code_reference': any(marker in response for marker in ['`', 'class', 'method', 'function', 'In `']),
        'not_truncated': '...' not in response[-50:],
        'coherent': response.count('.') > 2  # Has multiple sentences
    }
    return checks, all(checks.values())


def validate_single_file_gen(response):
    """Validate single-file code generation: should have SEARCH/REPLACE blocks."""
    checks = {
        'has_search_marker': '<<<< SEARCH' in response or '--- a/' in response,
        'has_replace_marker': '>>>> REPLACE' in response or '+++ b/' in response,
        'has_file_reference': 'File:' in response or 'file:' in response.lower(),
        'not_empty': len(response) > 200
    }
    return checks, all(checks.values())


def validate_multi_file_gen(response):
    """Validate multi-file generation: should have multiple file references."""
    file_count = response.count('File:') + response.count('file:')
    search_count = response.count('<<<< SEARCH')
    
    checks = {
        'multiple_files': file_count >= 2 or search_count >= 2,
        'has_search_replace': '<<<< SEARCH' in response or '--- a/' in response,
        'substantial_content': len(response) > 500
    }
    return checks, all(checks.values())


def validate_debugging_rca(response):
    """Validate debugging/RCA: should identify issue and suggest fix."""
    checks = {
        'identifies_issue': any(word in response.lower() for word in ['error', 'issue', 'problem', 'bug', 'cause']),
        'suggests_fix': any(word in response.lower() for word in ['fix', 'solution', 'resolve', 'change', 'update']),
        'has_code': '```' in response or '<<<< SEARCH' in response,
        'substantial': len(response) > 150
    }
    return checks, all(checks.values())


def validate_code_review(response):
    """Validate code review: should provide structured feedback."""
    checks = {
        'has_review_structure': any(word in response for word in ['Summary', 'Positive', 'Observations', 'Recommendations']),
        'has_verdict': any(word in response for word in ['APPROVED', 'PASS', 'FAIL', 'Verdict']),
        'has_thinking': '<thinking>' in response or 'thinking' in response.lower(),
        'substantial': len(response) > 200
    }
    return checks, all(checks.values())


VALIDATORS = {
    'qa_knowledge': validate_qa_knowledge,
    'single_file_gen': validate_single_file_gen,
    'multi_file_gen': validate_multi_file_gen,
    'debugging_rca': validate_debugging_rca,
    'code_review': validate_code_review
}


def run_kpi3_evaluation(model, tokenizer, categorized_samples):
    """Run KPI 3 evaluation on categorized samples."""
    print(f"\n🧪 Running KPI 3 Evaluation...")
    print("=" * 80)
    
    results = {}
    stats = {}
    
    for use_case, samples in categorized_samples.items():
        print(f"\n📋 Testing {use_case}: {len(samples)} samples")
        
        use_case_results = []
        passed = 0
        
        for i, sample in enumerate(samples):
            prompt = format_prompt(sample['messages'], tokenizer)

            # Generate
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
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
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Validate
            validator = VALIDATORS.get(use_case)
            if validator:
                checks, passed_validation = validator(response)
                if passed_validation:
                    passed += 1
            else:
                checks, passed_validation = {}, False
            
            use_case_results.append({
                'sample_id': i,
                'prompt_length': len(prompt),
                'response_length': len(response),
                'inference_time': round(inference_time, 2),
                'checks': checks,
                'passed': passed_validation
            })
        
        pass_rate = (passed / len(samples)) * 100 if samples else 0
        results[use_case] = use_case_results
        stats[use_case] = {
            'total': len(samples),
            'passed': passed,
            'pass_rate': round(pass_rate, 2)
        }
        
        print(f"   ✓ {use_case}: {passed}/{len(samples)} passed ({pass_rate:.1f}%)")
    
    print("\n" + "=" * 80)
    return results, stats


def generate_report(results, stats):
    """Generate KPI 3 evaluation report."""
    use_cases_passed = sum(1 for s in stats.values() if s['pass_rate'] >= 80)
    total_use_cases = len(stats)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'kpi': 'KPI 3: System Prompt & Dataset Coverage',
        'target': '100% of use-cases pass (≥80% per use-case)',
        'use_cases_tested': total_use_cases,
        'summary': {
            'use_cases_passed': use_cases_passed,
            'use_cases_total': total_use_cases,
            'overall_pass_rate': round((use_cases_passed / total_use_cases) * 100, 2) if total_use_cases > 0 else 0
        },
        'per_use_case_stats': stats,
        'pass_fail': {
            'target_met': use_cases_passed == total_use_cases,
            'status': 'PASS' if use_cases_passed == total_use_cases else 'PARTIAL' if use_cases_passed >= 4 else 'FAIL'
        },
        'detailed_results': results
    }
    
    return report


def main():
    print("=" * 80)
    print("KPI 3: SYSTEM PROMPT & DATASET COVERAGE TEST")
    print("=" * 80)
    
    # Load categorized samples
    categorized_samples = load_categorized_samples(SAMPLES_PER_USE_CASE)
    
    # Load model
    print("\n🔧 Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(MERGED_MODEL_PATH)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        MERGED_MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Run evaluation
    results, stats = run_kpi3_evaluation(model, tokenizer, categorized_samples)
    
    # Generate report
    report = generate_report(results, stats)
    
    # Save
    output_path = Path(OUTPUT_DIR) / f"kpi3_coverage_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("KPI 3 EVALUATION SUMMARY")
    print("=" * 80)
    for use_case, stat in stats.items():
        status = "✅" if stat['pass_rate'] >= 80 else "❌"
        print(f"{status} {use_case}: {stat['pass_rate']}% ({stat['passed']}/{stat['total']})")
    print(f"\nOverall: {report['summary']['use_cases_passed']}/{report['summary']['use_cases_total']} use-cases passed")
    print(f"Status: {report['pass_fail']['status']}")
    print(f"\n📄 Report saved: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()

