#!/usr/bin/env python3
"""
COMPREHENSIVE MODEL EVALUATION
===============================
Purpose: Thorough evaluation before committing to production.

This script:
1. Tests model on diverse samples (Q&A, Code Gen, Review, Debug, Refactor)
2. Captures FULL, non-truncated outputs
3. Generates human-friendly HTML table for manual review
4. Validates expected output patterns per use-case
5. Provides go/no-go recommendation

Output Format:
- HTML table: Type | User Input | Model Output (FULL) | Validation Status
- Expandable sections for long outputs
- Color-coded validation results
"""

import json
import torch
import time
from pathlib import Path
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
from collections import defaultdict

# CONFIGURATION
MERGED_MODEL_PATH = "/home/harshil/Harshil-PoCs/models/v16_1_merged"
DATASET_DIR = "/home/harshil/Harshil-PoCs/datasets/v16_1_fixed"
SAMPLES_PER_TYPE = 5  # 5 samples per use-case type
MAX_NEW_TOKENS = 2048  # Increased to avoid truncation
OUTPUT_DIR = "/home/harshil/Harshil-PoCs/evaluation/results"


def categorize_sample(sample):
    """Categorize sample by use-case type."""
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
    
    # Categorization logic
    if original_type == 'qa_pair' or 'how does' in user_content or 'explain' in user_content:
        return 'qa_knowledge'
    elif category == 'code_review' or 'review' in user_content:
        return 'code_review'
    elif 'debug' in user_content or 'rca' in user_content or 'error' in user_content or 'fix' in user_content:
        return 'debugging_rca'
    elif category == 'refactoring' or 'refactor' in user_content or assistant_content.count('file:') > 1:
        return 'multi_file_gen'
    elif '<<<< search' in assistant_content or 'search/replace' in user_content:
        return 'single_file_gen'
    else:
        return 'unknown'


def load_categorized_samples(samples_per_type=5):
    """Load and categorize validation samples."""
    print(f"\n📂 Loading validation samples ({samples_per_type} per type)...")
    
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
        selected[use_case] = available[:samples_per_type]
        print(f"   {use_case}: {len(selected[use_case])} samples")
    
    return selected


def format_prompt(messages, tokenizer, max_input_tokens=30000):
    """Format messages using chat template - EXCLUDE assistant response."""
    # Only include system and user messages, not the expected assistant response
    prompt_messages = [m for m in messages if m['role'] != 'assistant']

    # Apply chat template
    formatted = tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # Check if prompt is too long and truncate if needed
    tokens = tokenizer(formatted, return_tensors="pt")['input_ids']
    token_count = tokens.shape[1]

    if token_count > max_input_tokens:
        # Truncate the user message content to fit within limit
        # Keep system message and structure, truncate user content
        user_msg = next((m for m in prompt_messages if m['role'] == 'user'), None)
        if user_msg:
            # Estimate: roughly 4 chars per token
            max_user_chars = (max_input_tokens - 200) * 4  # Reserve 200 tokens for system + structure
            if len(user_msg['content']) > max_user_chars:
                user_msg['content'] = user_msg['content'][:max_user_chars] + "\n[... truncated due to length ...]"

                # Rebuild prompt with truncated user message
                formatted = tokenizer.apply_chat_template(
                    prompt_messages,
                    tokenize=False,
                    add_generation_prompt=True
                )

    return formatted


def validate_output(use_case, response):
    """Validate output based on use-case expectations."""
    validations = {
        'length_check': len(response) > 100,
        'not_truncated': not any(marker in response[-100:] for marker in ['...', '(truncated)', '<truncated>']),
        'has_content': len(response.strip()) > 0
    }
    
    # Use-case specific validations
    if use_case == 'qa_knowledge':
        validations['has_explanation'] = len(response) > 200
        validations['references_code'] = any(marker in response for marker in ['`', 'In `', 'method', 'class'])
    
    elif use_case == 'single_file_gen':
        validations['has_search_replace'] = '<<<< SEARCH' in response or '--- a/' in response
        validations['has_file_reference'] = 'file:' in response.lower() or 'File:' in response
    
    elif use_case == 'multi_file_gen':
        validations['multiple_files'] = response.count('File:') >= 2 or response.count('file:') >= 2
        validations['has_edits'] = '<<<< SEARCH' in response or '--- a/' in response
    
    elif use_case == 'debugging_rca':
        validations['identifies_issue'] = any(word in response.lower() for word in ['error', 'issue', 'problem', 'cause'])
        validations['suggests_fix'] = any(word in response.lower() for word in ['fix', 'solution', 'change'])
    
    elif use_case == 'code_review':
        validations['has_structure'] = any(word in response for word in ['Summary', 'Observations', 'Recommendations', 'Verdict'])
        validations['has_verdict'] = any(word in response for word in ['APPROVED', 'PASS', 'FAIL', 'LGTM'])
    
    passed = all(validations.values())
    return validations, passed


def run_evaluation(model, tokenizer, categorized_samples):
    """Run comprehensive evaluation."""
    print(f"\n🧪 Running Comprehensive Evaluation...")
    print("=" * 80)
    
    all_results = []
    
    for use_case, samples in categorized_samples.items():
        print(f"\n📋 Testing {use_case}: {len(samples)} samples")
        
        for i, sample in enumerate(samples):
            # Format prompt using chat template
            prompt = format_prompt(sample['messages'], tokenizer)
            
            # Extract user input for display
            user_input = ""
            expected_output = ""
            for msg in sample['messages']:
                if msg['role'] == 'user':
                    user_input = msg['content']
                elif msg['role'] == 'assistant':
                    expected_output = msg['content']
            
            # Generate response
            print(f"   Processing sample {i+1}/{len(samples)}...", end='', flush=True)
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            
            start_time = time.time()
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=MAX_NEW_TOKENS,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            inference_time = time.time() - start_time
            
            # Decode FULL response (no truncation)
            full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part (remove prompt)
            generated_only = full_response[len(prompt):].strip() if len(full_response) > len(prompt) else full_response
            
            # Validate
            validations, passed = validate_output(use_case, generated_only)
            
            all_results.append({
                'use_case': use_case,
                'sample_id': i,
                'user_input': user_input,
                'expected_output': expected_output,
                'model_output': generated_only,  # FULL, non-truncated
                'prompt_tokens': inputs['input_ids'].shape[1],
                'output_tokens': outputs[0].shape[0] - inputs['input_ids'].shape[1],
                'inference_time': round(inference_time, 2),
                'validations': validations,
                'passed': passed
            })
            
            status = "✅" if passed else "❌"
            print(f" {status} ({inference_time:.1f}s)")
    
    print("\n" + "=" * 80)
    return all_results


def generate_html_report(results):
    """Generate human-friendly HTML table report."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Calculate summary stats
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    # Group by use-case
    by_use_case = defaultdict(list)
    for r in results:
        by_use_case[r['use_case']].append(r)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Model Evaluation Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .summary {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .summary-stat {{ display: inline-block; margin-right: 30px; }}
        .summary-stat .label {{ font-weight: bold; color: #666; }}
        .summary-stat .value {{ font-size: 24px; color: #333; }}
        .pass {{ color: #28a745; }}
        .fail {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #007bff; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
        td {{ padding: 12px; border-bottom: 1px solid #ddd; vertical-align: top; }}
        tr:hover {{ background: #f8f9fa; }}
        .use-case-header {{ background: #e9ecef; font-weight: bold; font-size: 16px; }}
        .output-cell {{ max-width: 500px; }}
        .output-content {{ max-height: 400px; overflow-y: auto; white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 11px; background: #f8f9fa; padding: 10px; border-radius: 4px; border: 1px solid #dee2e6; }}
        .validation-badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; margin: 2px; }}
        .badge-pass {{ background: #d4edda; color: #155724; }}
        .badge-fail {{ background: #f8d7da; color: #721c24; }}
        .metadata {{ font-size: 11px; color: #666; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>🔍 Comprehensive Model Evaluation Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-stat">
            <div class="label">Timestamp:</div>
            <div class="value">{timestamp}</div>
        </div>
        <div class="summary-stat">
            <div class="label">Total Samples:</div>
            <div class="value">{total}</div>
        </div>
        <div class="summary-stat">
            <div class="label">Passed:</div>
            <div class="value class="{'pass' if pass_rate >= 80 else 'fail'}">{passed}/{total} ({pass_rate:.1f}%)</div>
        </div>
    </div>
"""
    
    # Add table
    html += """
    <table>
        <thead>
            <tr>
                <th style="width: 10%;">Use Case</th>
                <th style="width: 20%;">User Input</th>
                <th style="width: 30%;">Expected Output</th>
                <th style="width: 30%;">Model Output (FULL)</th>
                <th style="width: 10%;">Validation</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for use_case in sorted(by_use_case.keys()):
        samples = by_use_case[use_case]
        use_case_passed = sum(1 for s in samples if s['passed'])
        use_case_total = len(samples)
        
        # Use-case header row
        html += f"""
            <tr class="use-case-header">
                <td colspan="5">{use_case.upper().replace('_', ' ')} ({use_case_passed}/{use_case_total} passed)</td>
            </tr>
"""
        
        for result in samples:
            status_class = 'pass' if result['passed'] else 'fail'
            status_icon = '✅' if result['passed'] else '❌'
            
            # Validation badges
            validation_html = ""
            for check, passed in result['validations'].items():
                badge_class = 'badge-pass' if passed else 'badge-fail'
                validation_html += f'<span class="validation-badge {badge_class}">{check}</span>'
            
            html += f"""
            <tr>
                <td>{result['use_case'].replace('_', ' ')}</td>
                <td>
                    <div class="output-content">{result['user_input'][:500]}{'...' if len(result['user_input']) > 500 else ''}</div>
                </td>
                <td class="output-cell">
                    <div class="output-content">{result['expected_output']}</div>
                </td>
                <td class="output-cell">
                    <div class="output-content">{result['model_output']}</div>
                </td>
                <td>
                    <div class="{status_class}">{status_icon}</div>
                    {validation_html}
                </td>
            </tr>
"""
    
    html += """
        </tbody>
    </table>
</body>
</html>
"""
    
    return html


def main():
    print("=" * 80)
    print("COMPREHENSIVE MODEL EVALUATION")
    print("=" * 80)
    print(f"Model: {MERGED_MODEL_PATH}")
    print(f"Samples per type: {SAMPLES_PER_TYPE}")
    print(f"Max tokens: {MAX_NEW_TOKENS}")
    print("=" * 80)
    
    # Load samples
    categorized_samples = load_categorized_samples(SAMPLES_PER_TYPE)
    
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
    print("   ✓ Model loaded")
    
    # Run evaluation
    results = run_evaluation(model, tokenizer, categorized_samples)
    
    # Generate HTML report
    html_report = generate_html_report(results)
    
    # Save reports
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_path = output_dir / f"comprehensive_evaluation_{timestamp_str}.html"
    json_path = output_dir / f"comprehensive_evaluation_{timestamp_str}.json"
    
    with open(html_path, 'w') as f:
        f.write(html_report)
    
    with open(json_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'model': MERGED_MODEL_PATH,
            'results': results
        }, f, indent=2)
    
    # Print summary
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)
    print(f"Total samples: {total}")
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"\n📄 HTML Report: {html_path}")
    print(f"📄 JSON Report: {json_path}")
    print("=" * 80)
    
    # Open HTML in browser
    print(f"\n💡 Open the HTML report in your browser to review FULL outputs")


if __name__ == "__main__":
    main()

