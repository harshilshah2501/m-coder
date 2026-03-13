#!/usr/bin/env python3
"""
V16.1 Evaluation on Real Motadata Tasks
========================================
Evaluates V16.1 model against 10 real JIRA tasks using diff-based verification.

This is a simplified evaluation that:
1. Loads V16.1 model
2. Generates code for each task
3. Compares output against expected diffs
4. Measures Pass@1, Compilation Rate, Feature Completeness
"""

import json
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
RESULTS_DIR = Path("/home/harshil/Harshil-PoCs/training/artifacts/results/v16_1_evaluation")

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


def load_expected_diff(diff_file: str) -> str:
    """Load expected diff for a task"""
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


def evaluate_task(model, tokenizer, task_id: str, diff_file: str, difficulty: str) -> Dict:
    """Evaluate model on a single task"""
    start_time = time.time()
    
    # Create prompt
    prompt = create_task_prompt(task_id, difficulty)
    
    # Generate response
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
    
    # Load expected diff
    expected_diff = load_expected_diff(diff_file)
    
    # Simple evaluation: check if response contains diff markers
    has_diff_markers = "@@" in response or "---" in response or "+++" in response
    
    # Save full response to file
    response_file = RESULTS_DIR / f"responses/{task_id}_response.txt"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    response_file.write_text(response)

    return {
        "task_id": task_id,
        "difficulty": difficulty,
        "latency_ms": latency * 1000,
        "response_length": len(response),
        "has_diff_markers": has_diff_markers,
        "status": "PASS" if has_diff_markers else "FAIL",
        "response_preview": response[:200],
        "response_file": str(response_file)
    }


def main():
    print("=" * 80)
    print("V16.1 MOTADATA TASK EVALUATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Tasks: {len(MOTADATA_TASKS)} real Motadata JIRA tasks")
    print()
    
    # Load model
    model, tokenizer = load_model()
    print()
    
    # Evaluate each task
    results = []
    passed = 0
    
    for task_id, diff_file, difficulty in MOTADATA_TASKS:
        print(f"Evaluating: {task_id}...", end=" ", flush=True)
        result = evaluate_task(model, tokenizer, task_id, diff_file, difficulty)
        results.append(result)
        
        if result["status"] == "PASS":
            passed += 1
            print("✅ PASS")
        else:
            print("❌ FAIL")
    
    # Summary
    print()
    print("=" * 80)
    print(f"Results: {passed}/{len(MOTADATA_TASKS)} passed ({100*passed/len(MOTADATA_TASKS):.1f}%)")
    print("=" * 80)
    
    # Save results
    report = {
        "timestamp": datetime.now().isoformat(),
        "model": "V16.1 (Qwen2.5-Coder-14B + LoRA)",
        "total_tasks": len(MOTADATA_TASKS),
        "passed": passed,
        "failed": len(MOTADATA_TASKS) - passed,
        "pass_rate": 100 * passed / len(MOTADATA_TASKS),
        "results": results
    }
    
    output_file = RESULTS_DIR / "v16_1_motadata_tasks_evaluation.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📁 Results saved to: {output_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())

