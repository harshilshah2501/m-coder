#!/usr/bin/env python3
"""
V16.1 Model Evaluation on Motadata-Bench
=========================================
Evaluates the V16.1 fine-tuned model against 10 real Motadata JIRA tasks.

This is the CORRECT evaluation approach - testing against real production code scenarios,
not generic synthetic examples.
"""

import json
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
RESULTS_DIR = Path("/home/harshil/Harshil-PoCs/training/artifacts/results/v16_1_evaluation")
DIFFS_DIR = Path("/home/harshil/Harshil-PoCs/evaluation/diffs")

# 10 Real Motadata Tasks (from previous benchmark runs)
MOTADATA_TASKS = [
    {
        "task_id": "e7e7246ba5e1_refactored_code_and_removed_loggers",
        "description": "Refactored code and removed debug loggers",
        "difficulty": "hard",
        "files": 4,
        "patterns": ["integration", "api", "flow", "config", "performance", "test"]
    },
    {
        "task_id": "ae62a0fa3b59_metric_plugin_assignment_via_tag",
        "description": "Metric Plugin Assignment via Tag",
        "difficulty": "hard",
        "files": 4,
        "patterns": ["vertx", "database", "api", "monitor", "notification"]
    },
    {
        "task_id": "1aa62e982e8e_motadata-7445_topology_testcases",
        "description": "Topology testcases parallelism",
        "difficulty": "high",
        "files": 3,
        "patterns": ["discovery", "ui", "rca", "test"]
    },
    {
        "task_id": "45f95bda687a_refactored_snmp",
        "description": "Refactored SNMP code",
        "difficulty": "high",
        "files": 4,
        "patterns": ["snmp", "api", "monitor", "auth"]
    },
    {
        "task_id": "a284e89f1632_dependency_query_processor_refactor",
        "description": "Dependency query processor refactor",
        "difficulty": "medium",
        "files": 2,
        "patterns": ["database", "api", "performance"]
    },
    {
        "task_id": "fc01bcc7e9ef_compliance_db_refactor",
        "description": "Compliance DB refactor",
        "difficulty": "medium",
        "files": 2,
        "patterns": ["database", "compliance"]
    },
    {
        "task_id": "da66bf5d58f0_netroute_manager_removal",
        "description": "NetRoute manager removal",
        "difficulty": "medium",
        "files": 2,
        "patterns": ["network", "refactor"]
    },
    {
        "task_id": "3fa1126b4799_mongodb_protocol_removal",
        "description": "MongoDB protocol removal",
        "difficulty": "medium",
        "files": 2,
        "patterns": ["database", "mongodb"]
    },
    {
        "task_id": "443c87d78326_polling_failed_template",
        "description": "Polling failed template",
        "difficulty": "high",
        "files": 3,
        "patterns": ["monitor", "template", "error-handling"]
    },
    {
        "task_id": "25441efe4d29_ssh_corner_cases",
        "description": "SSH corner cases handling",
        "difficulty": "hard",
        "files": 5,
        "patterns": ["ssh", "discovery", "error-handling"]
    }
]


def load_model():
    """Load V16.1 fine-tuned model with LoRA adapter"""
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


def load_task_diff(task_id: str) -> str:
    """Load the expected diff for a task"""
    # Map task_id to diff file
    diff_mapping = {
        "e7e7246ba5e1_refactored_code_and_removed_loggers": "diff_refactored_code_loggers.patch",
        "ae62a0fa3b59_metric_plugin_assignment_via_tag": "diff_metric_plugin_tag_assignment.patch",
        "1aa62e982e8e_motadata-7445_topology_testcases": "diff_topology_testcases_parallelism.patch",
        "45f95bda687a_refactored_snmp": "diff_refactored_snmp.patch",
        "a284e89f1632_dependency_query_processor_refactor": "diff_dependency_query_processor_refactor.patch",
        "fc01bcc7e9ef_compliance_db_refactor": "diff_compliance_db_refactor.patch",
        "da66bf5d58f0_netroute_manager_removal": "diff_netroute_manager_removal.patch",
        "3fa1126b4799_mongodb_protocol_removal": "diff_mongodb_protocol_removal.patch",
        "443c87d78326_polling_failed_template": "diff_polling_failed_template.patch",
        "25441efe4d29_ssh_corner_cases": "diff_ssh_corner_cases.patch"
    }
    
    diff_file = DIFFS_DIR / diff_mapping.get(task_id, f"{task_id}.patch")
    if diff_file.exists():
        return diff_file.read_text()
    return ""


def create_task_prompt(task: Dict, diff_content: str) -> str:
    """Create a prompt for the model based on the task"""
    prompt = f"""You are a Motadata AIOps code assistant. Complete the following production task:

Task: {task['description']}
Difficulty: {task['difficulty']}
Files to modify: {task['files']}
Patterns: {', '.join(task['patterns'])}

Generate the code changes needed to complete this task. Provide a unified diff format showing the changes.

Expected output format:
```diff
[your diff here]
```
"""
    return prompt


def main():
    print("=" * 80)
    print("V16.1 MOTADATA-BENCH EVALUATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Base Model: {BASE_MODEL}")
    print(f"LoRA Adapter: {LORA_ADAPTER}")
    print(f"Tasks: {len(MOTADATA_TASKS)} real Motadata JIRA tasks")
    print()
    
    # Load model
    model, tokenizer = load_model()
    print()
    
    # TODO: Implement task execution
    # This requires integration with the Motadata sandbox environment
    # For now, we'll create a placeholder evaluation
    
    print("⚠️  IMPORTANT: Full Motadata-Bench evaluation requires:")
    print("   1. Motadata sandbox Docker container")
    print("   2. Task executor infrastructure")
    print("   3. Compilation + verification scripts")
    print()
    print("📋 Next steps:")
    print("   1. Locate the Motadata-Bench task executor")
    print("   2. Integrate V16.1 model with the executor")
    print("   3. Run full benchmark with compilation verification")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())

