#!/usr/bin/env python3
"""
Improved V16.1 Evaluation v2
============================
Addresses critical gaps from deep analysis:
1. Context-aware prompts with file paths, commit messages
2. Diff-aware metrics (not full-file compilation)
3. Better similarity scoring using diff structure
"""

import json
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Paths
BASE_MODEL = "Qwen/Qwen2.5-Coder-14B-Instruct"
LORA_ADAPTER = "/home/harshil/Harshil-PoCs/models/v16_1_finetuned"
DIFFS_DIR = Path("/home/harshil/Harshil-PoCs/evaluation/diffs")
RESULTS_DIR = Path("/home/harshil/Harshil-PoCs/training/artifacts/results/v16_1_improved_v2")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESPONSES_DIR = RESULTS_DIR / "responses"
RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

# Task definitions with context extracted from actual diffs
MOTADATA_TASKS = [
    {
        "id": "e7e7246ba5e1_refactored_code_and_removed_loggers",
        "diff_file": "diff_refactored_code_loggers.patch",
        "difficulty": "hard",
        "commit_msg": "Refactor code and remove unnecessary loggers",
        "files": [
            "motadata/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java",
            "motadata/src/main/java/com/mindarray/config/ConfigResponseProcessor.java",
            "motadata/src/main/java/com/mindarray/integration/IntegrationEngine.java",
            "motadata/src/main/java/com/mindarray/policy/EventPolicyInspector.java"
        ],
        "package": "com.mindarray"
    },
    {
        "id": "ae62a0fa3b59_metric_plugin_assignment_via_tag",
        "diff_file": "diff_metric_plugin_tag_assignment.patch",
        "difficulty": "hard",
        "commit_msg": "Implement metric plugin assignment via tag-based routing",
        "files": [
            "motadata/src/main/java/com/mindarray/api/MetricPlugin.java",
            "motadata/src/main/java/com/mindarray/eventbus/LocalEventChangeNotificationHandler.java",
            "motadata/src/main/java/com/mindarray/nms/MetricPoller.java",
            "motadata/src/main/resources/entity-schemas/metric-plugins.json"
        ],
        "package": "com.mindarray"
    },
    {
        "id": "1aa62e982e8e_motadata-7445_topology_testcases",
        "diff_file": "diff_topology_testcases_parallelism.patch",
        "difficulty": "high",
        "commit_msg": "Add topology test cases with parallel execution support",
        "files": [
            "motadata/src/test/java/com/mindarray/suite/RunbookSuite.java",
            "motadata/src/test/java/com/mindarray/topology/TestTopology.java",
            "motadata/src/test/java/com/mindarray/topology/TestTopologyPlugins.java",
            "motadata/src/test/java/com/mindarray/topology/TestTopologyScanner.java"
        ],
        "package": "com.mindarray"
    },
    {
        "id": "45f95bda687a_refactored_snmp",
        "diff_file": "diff_refactored_snmp.patch",
        "difficulty": "high",
        "commit_msg": "Refactor SNMP handling for better performance",
        "files": [
            "motadata/src/main/java/com/mindarray/api/RunbookPlugin.java",
            "motadata/src/main/java/com/mindarray/api/SNMPDeviceCatalog.java",
            "motadata/src/main/java/com/mindarray/api/UserProfile.java",
            "motadata/src/main/java/com/mindarray/util/DataSecurity.java"
        ],
        "package": "com.mindarray"
    },
    {
        "id": "a284e89f1632_dependency_query_processor_refactor",
        "diff_file": "diff_dependency_query_processor_refactor.patch",
        "difficulty": "medium",
        "commit_msg": "Refactor dependency query processor for topology engine",
        "files": [
            "motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java",
            "motadata/src/main/java/com/mindarray/api/DependencyMapper.java",
            "motadata/src/main/java/com/mindarray/eventbus/EventBusConstants.java",
            "motadata/src/main/java/com/mindarray/nms/TopologyEngine.java"
        ],
        "package": "com.mindarray"
    },
    {
        "id": "fc01bcc7e9ef_compliance_db_refactor",
        "diff_file": "diff_compliance_db_refactor.patch",
        "difficulty": "medium",
        "commit_msg": "Refactor: Rename package from compliance to db, update imports",
        "files": [
            "motadata/src/main/java/com/mindarray/Bootstrap.java",
            "motadata/src/main/java/com/mindarray/compliance/ComplianceDBService.java",
            "motadata/src/main/java/com/mindarray/db/ComplianceDBService.java",
            "motadata/src/main/java/com/mindarray/db/DBServiceProvider.java"
        ],
        "package": "com.mindarray"
    },
    {
        "id": "da66bf5d58f0_netroute_manager_removal",
        "diff_file": "diff_netroute_manager_removal.patch",
        "difficulty": "medium",
        "commit_msg": "Remove NetRouteManager and related configurations",
        "files": [
            "motadata/src/main/java/com/mindarray/BootstrapPrimary.java",
            "motadata/src/main/java/com/mindarray/BootstrapStandalone.java",
            "motadata/src/main/java/com/mindarray/util/MotadataConfigUtil.java"
        ],
        "package": "com.mindarray"
    },
    {
        "id": "3fa1126b4799_mongodb_protocol_removal",
        "diff_file": "diff_mongodb_protocol_removal.patch",
        "difficulty": "medium",
        "commit_msg": "Remove MongoDB protocol support from credential profiles",
        "files": [
            "motadata/db-files/dashboard-widgets/mongodb.json",
            "motadata/src/main/java/com/mindarray/nms/NMSConstants.java",
            "motadata/src/main/resources/entity-schemas/credential-profiles.json",
            "motadata/src/main/resources/entity-schemas/templates.json"
        ],
        "package": "com.mindarray"
    },
    {
        "id": "443c87d78326_polling_failed_template",
        "diff_file": "diff_polling_failed_template.patch",
        "difficulty": "high",
        "commit_msg": "Add polling failed notification template for Slack/Teams",
        "files": [
            "motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java",
            "motadata/src/main/java/com/mindarray/integration/SlackIntegration.java",
            "motadata/src/main/java/com/mindarray/integration/TeamsIntegration.java",
            "motadata/src/main/java/com/mindarray/notification/Notification.java"
        ],
        "package": "com.mindarray"
    },
    {
        "id": "25441efe4d29_ssh_corner_cases",
        "diff_file": "diff_ssh_corner_cases.patch",
        "difficulty": "hard",
        "commit_msg": "Handle SSH corner cases and connection edge scenarios",
        "files": [
            "motadata/src/main/java/com/mindarray/config/SSHClientManager.java",
            "motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java",
            "motadata/src/test/java/com/mindarray/ssh/TestSSHClientManager.java"
        ],
        "package": "com.mindarray"
    }
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


def create_context_aware_prompt(task: Dict) -> str:
    """Create prompt with full codebase context"""
    files_list = "\n".join(f"  - {f}" for f in task['files'])

    return f"""You are a Motadata Java developer. Complete this production task by generating a unified diff.

## Task Information
- **Task ID**: {task['id']}
- **Commit Message**: {task['commit_msg']}
- **Difficulty**: {task['difficulty']}
- **Package**: {task['package']}

## Files to Modify
{files_list}

## Instructions
Generate the code changes in **unified diff format** with proper file paths.
Use the exact file paths listed above with `a/` and `b/` prefixes.
Include `---`, `+++`, and `@@` markers for each change.

## Output Format Example
```diff
--- a/motadata/src/main/java/com/mindarray/example/Example.java
+++ b/motadata/src/main/java/com/mindarray/example/Example.java
@@ -10,6 +10,7 @@ package com.mindarray.example;
 import com.mindarray.util.Logger;
+import com.mindarray.util.NewImport;
```

Generate the unified diff now:
"""


def load_expected_diff(diff_file: str) -> str:
    """Load expected diff content"""
    path = DIFFS_DIR / diff_file
    if path.exists():
        return path.read_text()
    return ""


def extract_diff_files(diff_text: str) -> set:
    """Extract file paths from diff with better parsing"""
    files = set()
    patterns = [
        r'^--- a/(.+)$',
        r'^\+\+\+ b/(.+)$',
        r'^diff --git a/(.+?) b/',
    ]

    for line in diff_text.split('\n'):
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                files.add(match.group(1))
                break

    return files


def analyze_diff_quality(response: str, expected_diff: str) -> Dict:
    """Diff-aware quality analysis"""
    # Check for diff structure
    has_diff_header = bool(re.search(r'^diff --git', response, re.MULTILINE))
    has_minus_header = bool(re.search(r'^--- [ab]/', response, re.MULTILINE))
    has_plus_header = bool(re.search(r'^\+\+\+ [ab]/', response, re.MULTILINE))
    has_hunk_header = bool(re.search(r'^@@ .+ @@', response, re.MULTILINE))

    # Count hunks
    hunk_count = len(re.findall(r'^@@ .+ @@', response, re.MULTILINE))

    # Check for proper Java patterns in diff
    has_java_imports = bool(re.search(r'^\+\s*import\s+', response, re.MULTILINE))
    has_java_package = bool(re.search(r'^\+\s*package\s+', response, re.MULTILINE))
    has_java_methods = bool(re.search(r'^\+\s*(public|private|protected)', response, re.MULTILINE))

    # Extract files
    generated_files = extract_diff_files(response)
    expected_files = extract_diff_files(expected_diff)

    # Calculate file coverage
    if expected_files:
        matched = generated_files & expected_files
        file_coverage = len(matched) / len(expected_files)
    else:
        file_coverage = 0.0

    # Diff structure score
    structure_score = sum([
        has_diff_header * 0.15,
        has_minus_header * 0.20,
        has_plus_header * 0.20,
        has_hunk_header * 0.25,
        (hunk_count > 0) * 0.10,
        has_java_imports * 0.05,
        has_java_methods * 0.05,
    ])

    return {
        'has_diff_header': has_diff_header,
        'has_minus_header': has_minus_header,
        'has_plus_header': has_plus_header,
        'has_hunk_header': has_hunk_header,
        'hunk_count': hunk_count,
        'has_java_imports': has_java_imports,
        'has_java_package': has_java_package,
        'has_java_methods': has_java_methods,
        'generated_files': sorted(list(generated_files)),
        'expected_files': sorted(list(expected_files)),
        'matched_files': sorted(list(generated_files & expected_files)),
        'file_coverage': file_coverage,
        'structure_score': structure_score,
        'is_valid_diff': structure_score >= 0.6
    }


def calculate_diff_similarity(expected: str, generated: str) -> float:
    """Calculate similarity focused on diff content"""
    # Extract only diff lines (starting with + or -)
    def extract_change_lines(text):
        lines = set()
        for line in text.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                lines.add(line[1:].strip())
            elif line.startswith('-') and not line.startswith('---'):
                lines.add(line[1:].strip())
        return lines

    expected_changes = extract_change_lines(expected)
    generated_changes = extract_change_lines(generated)

    if not expected_changes:
        return 0.0

    intersection = expected_changes & generated_changes

    precision = len(intersection) / len(generated_changes) if generated_changes else 0
    recall = len(intersection) / len(expected_changes) if expected_changes else 0

    # F1 score
    if precision + recall > 0:
        return 2 * (precision * recall) / (precision + recall)
    return 0.0



def evaluate_task(model, tokenizer, task: Dict) -> Dict:
    """Evaluate a single task with context-aware prompt"""
    print(f"  Generating...", end=" ", flush=True)
    start_time = time.time()

    # Create context-aware prompt
    prompt = create_context_aware_prompt(task)

    # Generate
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=2500,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    latency = time.time() - start_time

    # Save response
    response_file = RESPONSES_DIR / f"{task['id']}.txt"
    response_file.write_text(response)

    print(f"({latency:.1f}s)", end=" ", flush=True)

    # Load expected diff
    expected_diff = load_expected_diff(task['diff_file'])

    # Analyze
    print("Analyzing...", end=" ", flush=True)
    diff_quality = analyze_diff_quality(response, expected_diff)
    similarity = calculate_diff_similarity(expected_diff, response)

    # Overall quality score
    quality_score = (
        diff_quality['structure_score'] * 0.35 +
        diff_quality['file_coverage'] * 0.35 +
        similarity * 0.30
    )

    return {
        'task_id': task['id'],
        'difficulty': task['difficulty'],
        'latency_ms': latency * 1000,
        'response_length': len(response),
        'response_file': str(response_file),
        'diff_quality': diff_quality,
        'similarity_score': similarity,
        'quality_score': quality_score,
        'pass_improved': (
            diff_quality['is_valid_diff'] and
            diff_quality['file_coverage'] >= 0.5
        )
    }


def main():
    print("=" * 80)
    print("IMPROVED V16.1 EVALUATION v2 - Context-Aware Prompts")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Tasks: {len(MOTADATA_TASKS)}")
    print(f"Output: {RESULTS_DIR}")
    print()
    print("Improvements:")
    print("  ✓ Context-aware prompts with file paths")
    print("  ✓ Diff-aware quality metrics (not compilation)")
    print("  ✓ Better similarity scoring using diff structure")
    print()

    # Load model
    model, tokenizer = load_model()
    print()

    # Evaluate
    results = []
    for i, task in enumerate(MOTADATA_TASKS, 1):
        print(f"[{i}/{len(MOTADATA_TASKS)}] {task['id'][:45]}...", end=" ")
        result = evaluate_task(model, tokenizer, task)
        results.append(result)

        status = "✅" if result['pass_improved'] else "⚠️"
        cov = result['diff_quality']['file_coverage']
        print(f"{status} Q={result['quality_score']:.2f} Cov={cov:.0%}")

    # Aggregate
    total = len(results)
    metrics = {
        'valid_diff_rate': sum(1 for r in results if r['diff_quality']['is_valid_diff']) / total,
        'avg_file_coverage': sum(r['diff_quality']['file_coverage'] for r in results) / total,
        'avg_structure_score': sum(r['diff_quality']['structure_score'] for r in results) / total,
        'avg_similarity': sum(r['similarity_score'] for r in results) / total,
        'avg_quality': sum(r['quality_score'] for r in results) / total,
        'improved_pass_rate': sum(1 for r in results if r['pass_improved']) / total,
    }

    # Report
    report = {
        'timestamp': datetime.now().isoformat(),
        'model': 'V16.1 (Qwen2.5-Coder-14B + LoRA)',
        'evaluation_version': 'v2_context_aware',
        'total_tasks': total,
        'metrics': metrics,
        'improvements': [
            'Context-aware prompts with file paths and commit messages',
            'Diff-structure validation instead of compilation heuristics',
            'File coverage measurement',
            'Diff-focused similarity scoring'
        ],
        'results': results
    }

    # Save
    output_file = RESULTS_DIR / "improved_evaluation_v2.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    # Summary
    print()
    print("=" * 80)
    print("IMPROVED METRICS SUMMARY")
    print("=" * 80)
    print(f"Valid Diff Rate:        {metrics['valid_diff_rate']:.1%}")
    print(f"Avg File Coverage:      {metrics['avg_file_coverage']:.1%}")
    print(f"Avg Structure Score:    {metrics['avg_structure_score']:.2f}")
    print(f"Avg Similarity:         {metrics['avg_similarity']:.1%}")
    print(f"Avg Quality Score:      {metrics['avg_quality']:.2f}/1.0")
    print(f"Improved Pass Rate:     {metrics['improved_pass_rate']:.1%}")
    print("=" * 80)
    print(f"\n📁 Full report: {output_file}")
    print(f"📁 Responses: {RESPONSES_DIR}")

    return 0


if __name__ == "__main__":
    exit(main())

