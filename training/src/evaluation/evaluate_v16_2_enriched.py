#!/usr/bin/env python3
"""
V16.2 Enriched Benchmark - With File Context
=============================================
Tests model with actual file paths and code context from expected diffs
"""

import requests
import json
import time
import re
from pathlib import Path
from datetime import datetime

API_URL = "http://localhost:8081/v1/chat/completions"
DIFFS_DIR = Path("/home/harshil/Harshil-PoCs/evaluation/diffs")
RESULTS_DIR = Path("/home/harshil/Harshil-PoCs/evaluation/results")

# Tasks with enriched context extracted from actual diffs
ENRICHED_TASKS = [
    {
        "task_id": "e7e7246ba5e1_refactored_code_and_removed_loggers",
        "diff_file": "diff_refactored_code_loggers.patch",
        "difficulty": "hard",
        "commit_msg": "refactored code and removed loggers",
        "files": ["motadata/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java"],
        "context": """Remove debug loggers and TODO comments. Changes include:
1. Remove LOGGER.info("###sending for get" + context) from getActivePolicies()
2. Remove TODO comment about NCM Policy in Netroute
3. Remove dead code block for NETWORK_CONFIG category
4. Remove LOGGER.info("Printing all ticks") from tick processing
5. Clean up variable assignments and whitespace"""
    },
    {
        "task_id": "ae62a0fa3b59_metric_plugin_assignment_via_tag",
        "diff_file": "diff_metric_plugin_tag_assignment.patch",
        "difficulty": "hard",
        "commit_msg": "Metric Plugin Assignment via Tag",
        "files": ["motadata/src/main/java/com/mindarray/api/MetricPlugin.java"],
        "context": """Add Tag-based metric plugin assignment. Changes:
1. Add getObjectsByEntityType() helper method call
2. Change updatedIds.getLong(index) to updatedIds.getValue(index) 
3. Add TAG entity type check alongside GROUP in update condition
4. Update changelog with MOTADATA-7352 reference"""
    },
    {
        "task_id": "1aa62e982e8e_motadata-7445_topology_testcases",
        "diff_file": "diff_topology_testcases_parallelism.patch",
        "difficulty": "high",
        "commit_msg": "MOTADATA-7445: topology testcases with parallelism",
        "files": ["motadata/src/test/java/com/mindarray/discovery/DiscoveryTest.java"],
        "context": """Add topology discovery test cases with async handling"""
    },
    {
        "task_id": "45f95bda687a_refactored_snmp",
        "diff_file": "diff_refactored_snmp.patch",
        "difficulty": "high", 
        "commit_msg": "refactored SNMP handling",
        "files": ["motadata/src/main/java/com/mindarray/api/SNMPDeviceCatalog.java",
                  "motadata/src/main/java/com/mindarray/util/DataSecurity.java"],
        "context": """Refactor SNMP device catalog and data security modules"""
    },
    {
        "task_id": "3fa1126b4799_mongodb_protocol_removal",
        "diff_file": "diff_mongodb_protocol_removal.patch",
        "difficulty": "medium",
        "commit_msg": "Removed MongoDB protocol support",
        "files": ["motadata/src/main/java/com/mindarray/db/MongoDBHandler.java"],
        "context": """Remove deprecated MongoDB protocol implementation"""
    },
]

def extract_files_from_diff(diff_path: Path) -> list:
    """Extract file paths from a diff file"""
    if not diff_path.exists():
        return []
    content = diff_path.read_text()
    files = re.findall(r'diff --git a/(.+?) b/', content)
    return files

def create_enriched_prompt(task: dict) -> str:
    """Create prompt with full context"""
    files_list = "\n".join(f"  - {f}" for f in task['files'])
    return f"""Complete this Motadata AIOps production task:

**Task ID**: {task['task_id']}
**Commit Message**: {task['commit_msg']}
**Difficulty**: {task['difficulty']}

**Files to modify**:
{files_list}

**Task Description**:
{task['context']}

Generate the code changes in unified diff format. Include proper diff headers with file paths."""

def evaluate_task(task: dict) -> dict:
    """Evaluate a single task with enriched prompt"""
    print(f"\n[Task] {task['task_id'][:45]}... ({task['difficulty']})")
    
    prompt = create_enriched_prompt(task)
    
    payload = {
        "model": "motadata-coder",
        "messages": [
            {"role": "system", "content": "You are an expert Java developer for Motadata AIOps. Generate precise unified diffs."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,  # Lower temperature for more precise output
        "max_tokens": 1500   # Reduced to prevent gibberish
    }
    
    try:
        start = time.time()
        resp = requests.post(API_URL, json=payload, timeout=120)
        resp.raise_for_status()
        latency = time.time() - start
        
        result = resp.json()
        response = result['choices'][0]['message']['content']
        tokens = result['usage']['completion_tokens']
        
        # Check for expected files in response
        files_found = sum(1 for f in task['files'] if Path(f).name.replace('.java','') in response.lower())
        file_coverage = files_found / len(task['files']) * 100 if task['files'] else 0
        
        print(f"  ✓ {tokens} tokens, {latency:.1f}s, file coverage: {file_coverage:.0f}%")
        
        return {
            "task_id": task['task_id'],
            "difficulty": task['difficulty'],
            "status": "success",
            "latency": latency,
            "tokens": tokens,
            "file_coverage": file_coverage,
            "response": response
        }
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return {"task_id": task['task_id'], "status": "error", "error": str(e)}

def main():
    print("=" * 80)
    print("V16.2 ENRICHED BENCHMARK (With File Context)")
    print("=" * 80)
    print(f"Tasks: {len(ENRICHED_TASKS)} | Temp: 0.3 | Max Tokens: 1500")
    
    results = []
    for i, task in enumerate(ENRICHED_TASKS, 1):
        print(f"\n[{i}/{len(ENRICHED_TASKS)}]", end="")
        results.append(evaluate_task(task))
    
    # Summary
    successful = [r for r in results if r['status'] == 'success']
    avg_coverage = sum(r['file_coverage'] for r in successful) / len(successful) if successful else 0
    
    print("\n" + "=" * 80)
    print(f"ENRICHED BENCHMARK RESULTS")
    print(f"  Success: {len(successful)}/{len(results)}")
    print(f"  Avg File Coverage: {avg_coverage:.1f}%")
    print(f"  Avg Latency: {sum(r['latency'] for r in successful)/len(successful):.1f}s")
    
    # Save results
    output = RESULTS_DIR / f"v16_2_enriched_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output, 'w') as f:
        json.dump({"results": results, "avg_file_coverage": avg_coverage}, f, indent=2)
    print(f"  Saved: {output}")

if __name__ == "__main__":
    main()

