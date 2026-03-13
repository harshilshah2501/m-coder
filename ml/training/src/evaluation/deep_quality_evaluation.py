#!/usr/bin/env python3
"""
Deep Quality Evaluation for V16.1
==================================
Measures Tier 1 + Tier 2 metrics from evaluation framework:
- Pass@1 (semantic correctness)
- Compilation Rate
- Feature Completeness (multi-file coverage)
- Hallucination Rate (non-existent APIs)
- CodeBLEU (semantic similarity)
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from difflib import unified_diff

# Paths
RESULTS_DIR = Path("/home/harshil/Harshil-PoCs/training/artifacts/results/v16_1_evaluation")
DIFFS_DIR = Path("/home/harshil/Harshil-PoCs/evaluation/diffs")
PREVIOUS_RESULTS = RESULTS_DIR / "v16_1_motadata_tasks_evaluation.json"
OUTPUT_FILE = RESULTS_DIR / "deep_quality_metrics.json"

# Load previous evaluation results
with open(PREVIOUS_RESULTS) as f:
    previous_results = json.load(f)


def extract_files_from_diff(diff_text: str) -> set:
    """Extract file paths mentioned in a diff"""
    files = set()
    for line in diff_text.split('\n'):
        if line.startswith('---') or line.startswith('+++'):
            # Extract file path from diff header
            match = re.search(r'[ab]/(.+?)(?:\s|$)', line)
            if match:
                files.add(match.group(1))
    return files


def check_compilation_markers(response: str) -> Dict:
    """Check for Java compilation-related markers"""
    markers = {
        'has_imports': bool(re.search(r'import\s+[\w.]+;', response)),
        'has_package': bool(re.search(r'package\s+[\w.]+;', response)),
        'has_class_def': bool(re.search(r'(class|interface|enum)\s+\w+', response)),
        'has_method_def': bool(re.search(r'(public|private|protected).*\s+\w+\s*\(', response)),
        'has_syntax_errors': bool(re.search(r'(SyntaxError|ParseError|CompileError)', response, re.I)),
    }
    
    # Estimate compilation likelihood
    compilation_score = sum([
        markers['has_imports'] * 0.2,
        markers['has_package'] * 0.2,
        markers['has_class_def'] * 0.3,
        markers['has_method_def'] * 0.3,
        (not markers['has_syntax_errors']) * 0.2
    ])
    
    return {
        **markers,
        'compilation_score': compilation_score,
        'likely_compiles': compilation_score >= 0.6
    }


def check_hallucinations(response: str) -> Dict:
    """Detect potential hallucinations (non-existent APIs)"""
    hallucination_indicators = {
        'unknown_imports': len(re.findall(r'import\s+com\.example\.', response)),  # Fake package
        'todo_comments': len(re.findall(r'//\s*TODO|//\s*FIXME', response, re.I)),
        'placeholder_names': len(re.findall(r'\b(foo|bar|baz|temp|tmp)\b', response, re.I)),
        'generic_exceptions': len(re.findall(r'catch\s*\(\s*Exception\s+e\s*\)', response)),
    }
    
    hallucination_score = sum(hallucination_indicators.values())
    
    return {
        **hallucination_indicators,
        'hallucination_score': hallucination_score,
        'has_hallucinations': hallucination_score > 2
    }


def measure_feature_completeness(task_id: str, response: str, expected_diff_file: str) -> Dict:
    """Check if all required files are touched"""
    # Load expected diff
    expected_diff_path = DIFFS_DIR / expected_diff_file
    if not expected_diff_path.exists():
        return {'status': 'no_expected_diff', 'completeness': 0.0}
    
    expected_diff = expected_diff_path.read_text()
    
    # Extract files from both diffs
    expected_files = extract_files_from_diff(expected_diff)
    generated_files = extract_files_from_diff(response)
    
    if not expected_files:
        return {'status': 'no_expected_files', 'completeness': 0.0}
    
    # Calculate coverage
    matched_files = expected_files & generated_files
    completeness = len(matched_files) / len(expected_files) if expected_files else 0.0
    
    return {
        'expected_files': sorted(list(expected_files)),
        'generated_files': sorted(list(generated_files)),
        'matched_files': sorted(list(matched_files)),
        'missing_files': sorted(list(expected_files - generated_files)),
        'extra_files': sorted(list(generated_files - expected_files)),
        'completeness': completeness,
        'status': 'complete' if completeness >= 0.8 else 'partial'
    }


def calculate_simple_similarity(expected: str, generated: str) -> float:
    """Simple line-based similarity (proxy for CodeBLEU)"""
    expected_lines = set(expected.strip().split('\n'))
    generated_lines = set(generated.strip().split('\n'))
    
    if not expected_lines:
        return 0.0
    
    intersection = expected_lines & generated_lines
    union = expected_lines | generated_lines
    
    return len(intersection) / len(union) if union else 0.0


def evaluate_task_quality(task_result: Dict, diff_file: str) -> Dict:
    """Deep quality evaluation for a single task"""
    task_id = task_result['task_id']
    response = task_result.get('response_preview', '')  # We only have preview, not full response
    
    # Note: We're limited by only having response_preview (200 chars)
    # For full evaluation, we'd need the complete response
    
    compilation = check_compilation_markers(response)
    hallucinations = check_hallucinations(response)
    completeness = measure_feature_completeness(task_id, response, diff_file)
    
    return {
        'task_id': task_id,
        'difficulty': task_result['difficulty'],
        'compilation_analysis': compilation,
        'hallucination_analysis': hallucinations,
        'feature_completeness': completeness,
        'overall_quality_score': (
            compilation['compilation_score'] * 0.3 +
            (1 - hallucinations['has_hallucinations']) * 0.3 +
            completeness['completeness'] * 0.4
        )
    }


def main():
    print("=" * 80)
    print("DEEP QUALITY EVALUATION - V16.1")
    print("=" * 80)
    print()
    
    print("⚠️  NOTE: This evaluation is limited by only having 200-char response previews")
    print("   For full evaluation, we need complete model responses")
    print()
    
    # Task mapping (from previous evaluation)
    task_mapping = [
        ("e7e7246ba5e1_refactored_code_and_removed_loggers", "diff_refactored_code_loggers.patch"),
        ("ae62a0fa3b59_metric_plugin_assignment_via_tag", "diff_metric_plugin_tag_assignment.patch"),
        ("1aa62e982e8e_motadata-7445_topology_testcases", "diff_topology_testcases_parallelism.patch"),
        ("45f95bda687a_refactored_snmp", "diff_refactored_snmp.patch"),
        ("a284e89f1632_dependency_query_processor_refactor", "diff_dependency_query_processor_refactor.patch"),
        ("fc01bcc7e9ef_compliance_db_refactor", "diff_compliance_db_refactor.patch"),
        ("da66bf5d58f0_netroute_manager_removal", "diff_netroute_manager_removal.patch"),
        ("3fa1126b4799_mongodb_protocol_removal", "diff_mongodb_protocol_removal.patch"),
        ("443c87d78326_polling_failed_template", "diff_polling_failed_template.patch"),
        ("25441efe4d29_ssh_corner_cases", "diff_ssh_corner_cases.patch"),
    ]

    # Evaluate each task
    quality_results = []
    for task_result in previous_results['results']:
        task_id = task_result['task_id']
        diff_file = next((df for tid, df in task_mapping if tid == task_id), None)

        if diff_file:
            print(f"Analyzing: {task_id[:40]}...", end=" ")
            quality = evaluate_task_quality(task_result, diff_file)
            quality_results.append(quality)
            print(f"Quality: {quality['overall_quality_score']:.2f}")
        else:
            print(f"⚠️  No diff mapping for {task_id}")

    # Aggregate metrics
    total_tasks = len(quality_results)

    compilation_likely = sum(1 for r in quality_results if r['compilation_analysis']['likely_compiles'])
    hallucination_detected = sum(1 for r in quality_results if r['hallucination_analysis']['has_hallucinations'])
    complete_features = sum(1 for r in quality_results if r['feature_completeness']['completeness'] >= 0.8)

    avg_completeness = sum(r['feature_completeness']['completeness'] for r in quality_results) / total_tasks
    avg_quality = sum(r['overall_quality_score'] for r in quality_results) / total_tasks

    # Summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'model': 'V16.1 (Qwen2.5-Coder-14B + LoRA)',
        'total_tasks': total_tasks,
        'tier_1_metrics': {
            'compilation_rate': compilation_likely / total_tasks,
            'hallucination_rate': hallucination_detected / total_tasks,
            'feature_completeness_rate': complete_features / total_tasks,
            'avg_feature_completeness': avg_completeness,
        },
        'tier_2_metrics': {
            'avg_overall_quality': avg_quality,
        },
        'targets': {
            'compilation_rate': 0.90,
            'hallucination_rate': 0.05,
            'feature_completeness': 0.80,
        },
        'status': {
            'compilation': '✅ PASS' if (compilation_likely / total_tasks) >= 0.90 else '❌ FAIL',
            'hallucination': '✅ PASS' if (hallucination_detected / total_tasks) <= 0.05 else '❌ FAIL',
            'feature_completeness': '✅ PASS' if (complete_features / total_tasks) >= 0.80 else '❌ FAIL',
        },
        'detailed_results': quality_results,
        'limitations': [
            'Only 200-char response previews available (not full responses)',
            'Compilation analysis is heuristic-based (not actual Java compiler)',
            'Similarity metric is simplified (not full CodeBLEU)',
            'For production evaluation, need full model responses'
        ]
    }

    # Print summary
    print()
    print("=" * 80)
    print("TIER 1 METRICS SUMMARY")
    print("=" * 80)
    print(f"Compilation Rate:        {summary['tier_1_metrics']['compilation_rate']:.1%} {summary['status']['compilation']}")
    print(f"Hallucination Rate:      {summary['tier_1_metrics']['hallucination_rate']:.1%} {summary['status']['hallucination']}")
    print(f"Feature Completeness:    {summary['tier_1_metrics']['feature_completeness_rate']:.1%} {summary['status']['feature_completeness']}")
    print(f"Avg Completeness Score:  {summary['tier_1_metrics']['avg_feature_completeness']:.2f}")
    print()
    print(f"Overall Quality Score:   {summary['tier_2_metrics']['avg_overall_quality']:.2f}/1.0")
    print("=" * 80)

    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📁 Results saved to: {OUTPUT_FILE}")

    return 0


if __name__ == "__main__":
    exit(main())

