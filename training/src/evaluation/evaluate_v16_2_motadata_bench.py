#!/usr/bin/env python3
"""
V16.2 Comprehensive Motadata-Bench Evaluation
==============================================
Evaluates v16.2 model on 10 real-world Motadata tasks via RAG API
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
API_URL = "http://localhost:8081/v1/chat/completions"
DIFFS_DIR = Path("/home/harshil/Harshil-PoCs/evaluation/diffs")
RESULTS_DIR = Path("/home/harshil/Harshil-PoCs/evaluation/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

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

def load_expected_diff(diff_file: str) -> str:
    """Load expected diff from file"""
    diff_path = DIFFS_DIR / diff_file
    if diff_path.exists():
        return diff_path.read_text()
    return ""

def create_task_prompt(task_id: str, difficulty: str) -> str:
    """Create prompt for the model"""
    return f"""Complete this Motadata production task:

Task ID: {task_id}
Difficulty: {difficulty}

Generate the code changes needed. Provide output in unified diff format."""

def evaluate_task(task_id: str, difficulty: str) -> Dict:
    """Evaluate a single task"""
    print(f"\n[Task] {task_id} ({difficulty})")
    
    prompt = create_task_prompt(task_id, difficulty)
    
    payload = {
        "model": "motadata-coder",
        "messages": [
            {"role": "system", "content": "You are an expert Java code assistant for Motadata AIOps platform."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    try:
        start = time.time()
        resp = requests.post(API_URL, json=payload, timeout=120)
        resp.raise_for_status()
        latency = time.time() - start
        
        result = resp.json()
        response = result['choices'][0]['message']['content']
        tokens = result['usage']['completion_tokens']
        
        print(f"  ✓ Generated {tokens} tokens in {latency:.2f}s")
        
        return {
            "task_id": task_id,
            "difficulty": difficulty,
            "status": "success",
            "latency": latency,
            "tokens": tokens,
            "response": response
        }
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return {
            "task_id": task_id,
            "difficulty": difficulty,
            "status": "error",
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("V16.2 MOTADATA-BENCH EVALUATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Tasks: {len(MOTADATA_TASKS)} real Motadata JIRA tasks")
    print()
    
    results = []
    start_time = time.time()
    
    for i, (task_id, diff_file, difficulty) in enumerate(MOTADATA_TASKS, 1):
        print(f"\n[{i}/{len(MOTADATA_TASKS)}]", end=" ")
        result = evaluate_task(task_id, difficulty)
        results.append(result)
    
    total_time = time.time() - start_time
    
    # Summary
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'error')
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Tasks: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Avg Latency: {sum(r.get('latency', 0) for r in results) / successful:.2f}s" if successful > 0 else "N/A")
    
    # Save results
    output_file = RESULTS_DIR / f"v16_2_motadata_bench_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": "v16.2",
            "total_tasks": len(results),
            "successful": successful,
            "failed": failed,
            "total_time": total_time,
            "results": results
        }, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())

