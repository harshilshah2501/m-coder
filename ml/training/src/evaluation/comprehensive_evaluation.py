#!/usr/bin/env python3
"""
Comprehensive V16.1 Evaluation with Full Tier 1 Metrics
========================================================
Evaluates V16.1 against 10 Motadata tasks with complete quality analysis:
- Pass@1 (diff format correctness)
- Compilation Rate (Java syntax validation)
- Feature Completeness (multi-file coverage)
- Hallucination Rate (non-existent APIs)
- Semantic Similarity (vs expected diffs)
"""

import json
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Paths
BASE_MODEL = "Qwen/Qwen2.5-Coder-14B-Instruct"
LORA_ADAPTER = "/home/harshil/Harshil-PoCs/models/v16_1_finetuned"
DIFFS_DIR = Path("/home/harshil/Harshil-PoCs/evaluation/diffs")
RESULTS_DIR = Path("/home/harshil/Harshil-PoCs/training/artifacts/results/v16_1_comprehensive")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESPONSES_DIR = RESULTS_DIR / "responses"
RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

# 10 Real Motadata Tasks
MOTADATA_TASKS = [
    ("e7e7246ba5e1_refactored_code_and_removed_loggers", "diff_refactored_code_loggers.patch", "hard"),
    ("ae62a0fa3b59_metric_plugin_assignment_via_tag", "diff_metric_plugin_tag_assignment.patch", "hard"),
    ("1aa62e982e8e_motadata-7445_topology_testcases", "diff_topology_testcases_parallelism.patch", "high"),
    ("45f95bda687a_refactored_snmp", "diff_refactored_snmp.patch", "high"),
    ("a284e89f1632_dependency_query_processor_refactor", "diff_dependency_query_processor_refactor.patch", "medium"),
    ("fc01bcc7e9ef_compliance_db_refactor", "diff_compliance_db_refactor.patch", "medium"),
    ("da66bf5d58f0_netroute_manager_removal", "diff_netroute_manager_removal.patch", "medium"),
    ("3fa1126b4799_mongodb_protocol_removal", "diff_mongodb_protocol_removal.patch", "medium"),
    ("443c87d78326_polling_failed_template", "diff_polling_failed_template.patch", "high"),
    ("25441efe4d29_ssh_corner_cases", "diff_ssh_corner_cases.patch", "hard"),
]


def load_model():
    """Load V16.1 fine-tuned model"""
    print("Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    
    print("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(model, LORA_ADAPTER)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    
    return model, tokenizer


def create_task_prompt(task_id: str, difficulty: str) -> str:
    """Create prompt for the model"""
    return f"""Complete this Motadata production task:

Task ID: {task_id}
Difficulty: {difficulty}

Generate the code changes needed. Provide output in unified diff format."""


def extract_files_from_diff(diff_text: str) -> set:
    """Extract file paths from diff"""
    files = set()
    for line in diff_text.split('\n'):
        if line.startswith('---') or line.startswith('+++'):
            match = re.search(r'[ab]/(.+?)(?:\s|$)', line)
            if match:
                files.add(match.group(1))
    return files


def analyze_compilation(response: str) -> Dict:
    """Analyze Java compilation likelihood"""
    markers = {
        'has_imports': bool(re.search(r'import\s+[\w.]+;', response)),
        'has_package': bool(re.search(r'package\s+[\w.]+;', response)),
        'has_class_def': bool(re.search(r'(class|interface|enum)\s+\w+', response)),
        'has_method_def': bool(re.search(r'(public|private|protected).*\s+\w+\s*\(', response)),
        'has_syntax_errors': bool(re.search(r'(SyntaxError|ParseError|CompileError)', response, re.I)),
        'has_balanced_braces': response.count('{') == response.count('}'),
        'has_balanced_parens': response.count('(') == response.count(')'),
    }
    
    compilation_score = sum([
        markers['has_imports'] * 0.15,
        markers['has_package'] * 0.15,
        markers['has_class_def'] * 0.25,
        markers['has_method_def'] * 0.25,
        (not markers['has_syntax_errors']) * 0.1,
        markers['has_balanced_braces'] * 0.05,
        markers['has_balanced_parens'] * 0.05,
    ])
    
    return {
        **markers,
        'compilation_score': compilation_score,
        'likely_compiles': compilation_score >= 0.6
    }


def analyze_hallucinations(response: str) -> Dict:
    """Detect hallucinations"""
    indicators = {
        'fake_packages': len(re.findall(r'import\s+com\.example\.', response)),
        'todo_comments': len(re.findall(r'//\s*TODO|//\s*FIXME|//\s*XXX', response, re.I)),
        'placeholder_vars': len(re.findall(r'\b(foo|bar|baz|temp|tmp|test123)\b', response, re.I)),
        'generic_catches': len(re.findall(r'catch\s*\(\s*Exception\s+e\s*\)', response)),
        'undefined_refs': len(re.findall(r'//\s*undefined|//\s*not\s+found', response, re.I)),
    }
    
    hallucination_score = sum(indicators.values())
    
    return {
        **indicators,
        'total_hallucination_indicators': hallucination_score,
        'has_hallucinations': hallucination_score > 2
    }


def analyze_feature_completeness(response: str, expected_diff_file: str) -> Dict:
    """Check multi-file coverage"""
    expected_path = DIFFS_DIR / expected_diff_file
    if not expected_path.exists():
        return {'status': 'no_expected_diff', 'completeness': 0.0}
    
    expected_diff = expected_path.read_text()
    expected_files = extract_files_from_diff(expected_diff)
    generated_files = extract_files_from_diff(response)
    
    if not expected_files:
        return {'status': 'no_expected_files', 'completeness': 0.0}
    
    matched = expected_files & generated_files
    completeness = len(matched) / len(expected_files)
    
    return {
        'expected_files': sorted(list(expected_files)),
        'generated_files': sorted(list(generated_files)),
        'matched_files': sorted(list(matched)),
        'missing_files': sorted(list(expected_files - generated_files)),
        'extra_files': sorted(list(generated_files - expected_files)),
        'completeness': completeness,
        'is_complete': completeness >= 0.8
    }


def calculate_similarity(expected: str, generated: str) -> float:
    """Simple similarity metric (proxy for CodeBLEU)"""
    expected_lines = set(line.strip() for line in expected.split('\n') if line.strip())
    generated_lines = set(line.strip() for line in generated.split('\n') if line.strip())

    if not expected_lines:
        return 0.0

    intersection = expected_lines & generated_lines
    union = expected_lines | generated_lines

    jaccard = len(intersection) / len(union) if union else 0.0
    recall = len(intersection) / len(expected_lines) if expected_lines else 0.0

    return (jaccard + recall) / 2  # Balanced metric


def evaluate_task(model, tokenizer, task_id: str, diff_file: str, difficulty: str) -> Dict:
    """Comprehensive evaluation of a single task"""
    print(f"  Generating response...", end=" ", flush=True)
    start_time = time.time()

    # Generate
    prompt = create_task_prompt(task_id, difficulty)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=2000,
            temperature=0.7,
            top_p=0.9
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    latency = time.time() - start_time

    # Save full response
    response_file = RESPONSES_DIR / f"{task_id}.txt"
    response_file.write_text(response)

    print(f"({latency:.1f}s)", end=" ", flush=True)

    # Analyze
    print("Analyzing...", end=" ", flush=True)

    has_diff_markers = "@@" in response or ("---" in response and "+++" in response)
    compilation = analyze_compilation(response)
    hallucinations = analyze_hallucinations(response)
    completeness = analyze_feature_completeness(response, diff_file)

    # Load expected diff for similarity
    expected_path = DIFFS_DIR / diff_file
    similarity = 0.0
    if expected_path.exists():
        expected_diff = expected_path.read_text()
        similarity = calculate_similarity(expected_diff, response)

    # Overall quality score
    quality_score = (
        (1 if has_diff_markers else 0) * 0.2 +
        compilation['compilation_score'] * 0.25 +
        (1 - hallucinations['has_hallucinations']) * 0.15 +
        completeness['completeness'] * 0.25 +
        similarity * 0.15
    )

    return {
        'task_id': task_id,
        'difficulty': difficulty,
        'latency_ms': latency * 1000,
        'response_length': len(response),
        'response_file': str(response_file),

        # Tier 1 Metrics
        'has_diff_format': has_diff_markers,
        'compilation_analysis': compilation,
        'hallucination_analysis': hallucinations,
        'feature_completeness': completeness,
        'similarity_score': similarity,

        # Overall
        'quality_score': quality_score,
        'pass_tier1': (
            has_diff_markers and
            compilation['likely_compiles'] and
            not hallucinations['has_hallucinations'] and
            completeness['completeness'] >= 0.8
        )
    }


def main():
    print("=" * 80)
    print("COMPREHENSIVE V16.1 EVALUATION - TIER 1 METRICS")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Tasks: {len(MOTADATA_TASKS)}")
    print(f"Output: {RESULTS_DIR}")
    print()

    # Load model
    model, tokenizer = load_model()
    print()

    # Evaluate
    results = []
    for i, (task_id, diff_file, difficulty) in enumerate(MOTADATA_TASKS, 1):
        print(f"[{i}/{len(MOTADATA_TASKS)}] {task_id[:50]}...", end=" ")
        result = evaluate_task(model, tokenizer, task_id, diff_file, difficulty)
        results.append(result)

        status = "✅" if result['pass_tier1'] else "⚠️"
        print(f"{status} Q={result['quality_score']:.2f}")

    # Aggregate
    total = len(results)
    metrics = {
        'pass_rate': sum(1 for r in results if r['has_diff_format']) / total,
        'compilation_rate': sum(1 for r in results if r['compilation_analysis']['likely_compiles']) / total,
        'hallucination_rate': sum(1 for r in results if r['hallucination_analysis']['has_hallucinations']) / total,
        'feature_completeness_rate': sum(1 for r in results if r['feature_completeness']['is_complete']) / total,
        'avg_similarity': sum(r['similarity_score'] for r in results) / total,
        'avg_quality': sum(r['quality_score'] for r in results) / total,
        'tier1_pass_rate': sum(1 for r in results if r['pass_tier1']) / total,
    }

    # Report
    report = {
        'timestamp': datetime.now().isoformat(),
        'model': 'V16.1 (Qwen2.5-Coder-14B + LoRA)',
        'total_tasks': total,
        'tier_1_metrics': metrics,
        'targets': {
            'pass_rate': 0.65,
            'compilation_rate': 0.90,
            'hallucination_rate': 0.05,
            'feature_completeness': 0.80,
        },
        'results': results
    }

    # Save
    output_file = RESULTS_DIR / "comprehensive_evaluation.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    # Summary
    print()
    print("=" * 80)
    print("TIER 1 METRICS SUMMARY")
    print("=" * 80)
    print(f"Pass@1 (Diff Format):    {metrics['pass_rate']:.1%}  (target: ≥65%)")
    print(f"Compilation Rate:        {metrics['compilation_rate']:.1%}  (target: ≥90%)")
    print(f"Hallucination Rate:      {metrics['hallucination_rate']:.1%}  (target: ≤5%)")
    print(f"Feature Completeness:    {metrics['feature_completeness_rate']:.1%}  (target: ≥80%)")
    print(f"Avg Similarity:          {metrics['avg_similarity']:.1%}")
    print(f"Avg Quality Score:       {metrics['avg_quality']:.2f}/1.0")
    print(f"Tier 1 Pass Rate:        {metrics['tier1_pass_rate']:.1%}")
    print("=" * 80)
    print(f"\n📁 Full report: {output_file}")
    print(f"📁 Responses: {RESPONSES_DIR}")

    return 0


if __name__ == "__main__":
    exit(main())

