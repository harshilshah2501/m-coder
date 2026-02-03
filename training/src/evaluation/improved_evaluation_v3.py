#!/usr/bin/env python3
"""
Improved V16.1 Evaluation v3: RAG + Few-shot + Example.java filter
"""

import json, re, time, httpx
from pathlib import Path
from datetime import datetime
from typing import Dict
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_MODEL = "Qwen/Qwen2.5-Coder-14B-Instruct"
LORA_ADAPTER = "/home/harshil/Harshil-PoCs/models/v16_1_finetuned"
DIFFS_DIR = Path("/home/harshil/Harshil-PoCs/evaluation/diffs")
RESULTS_DIR = Path("/home/harshil/Harshil-PoCs/training/artifacts/results/v16_1_improved_v3")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESPONSES_DIR = RESULTS_DIR / "responses"
RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
RAG_URL = "http://localhost:8081"

FEW_SHOT = """## Example
```diff
--- a/motadata/src/main/java/com/mindarray/api/RunbookPlugin.java
+++ b/motadata/src/main/java/com/mindarray/api/RunbookPlugin.java
@@ -399,7 +399,7 @@ public class RunbookPlugin extends AbstractAPI
-                    response.put(APIConstants.Entity.GROUP.getName(), DataSecurity.qualifyGroups(response.getLong(USER_ID), item.getJsonArray(RUNBOOK_PLUGIN_ENTITIES)));
+                    response.put(APIConstants.Entity.GROUP.getName(), DataSecurity.qualifyGroups(routingContext.user().principal().getLong(ID), item.getJsonArray(RUNBOOK_PLUGIN_ENTITIES)));
```
"""

TASKS = [
    {"id": "e7e7246ba5e1_refactored_code_and_removed_loggers", "diff_file": "diff_refactored_code_loggers.patch", "commit_msg": "Refactor code and remove unnecessary loggers", "files": ["motadata/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java", "motadata/src/main/java/com/mindarray/config/ConfigResponseProcessor.java", "motadata/src/main/java/com/mindarray/integration/IntegrationEngine.java", "motadata/src/main/java/com/mindarray/policy/EventPolicyInspector.java"]},
    {"id": "ae62a0fa3b59_metric_plugin_assignment_via_tag", "diff_file": "diff_metric_plugin_tag_assignment.patch", "commit_msg": "Implement metric plugin assignment via tag-based routing", "files": ["motadata/src/main/java/com/mindarray/api/MetricPlugin.java", "motadata/src/main/java/com/mindarray/eventbus/LocalEventChangeNotificationHandler.java", "motadata/src/main/java/com/mindarray/nms/MetricPoller.java", "motadata/src/main/resources/entity-schemas/metric-plugins.json"]},
    {"id": "1aa62e982e8e_motadata-7445_topology_testcases", "diff_file": "diff_topology_testcases_parallelism.patch", "commit_msg": "Add topology test cases with parallel execution", "files": ["motadata/src/test/java/com/mindarray/suite/RunbookSuite.java", "motadata/src/test/java/com/mindarray/topology/TestTopology.java", "motadata/src/test/java/com/mindarray/topology/TestTopologyPlugins.java", "motadata/src/test/java/com/mindarray/topology/TestTopologyScanner.java"]},
    {"id": "45f95bda687a_refactored_snmp", "diff_file": "diff_refactored_snmp.patch", "commit_msg": "Refactor SNMP handling", "files": ["motadata/src/main/java/com/mindarray/api/RunbookPlugin.java", "motadata/src/main/java/com/mindarray/api/SNMPDeviceCatalog.java", "motadata/src/main/java/com/mindarray/api/UserProfile.java", "motadata/src/main/java/com/mindarray/util/DataSecurity.java"]},
    {"id": "a284e89f1632_dependency_query_processor_refactor", "diff_file": "diff_dependency_query_processor_refactor.patch", "commit_msg": "Refactor dependency query processor", "files": ["motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java", "motadata/src/main/java/com/mindarray/api/DependencyMapper.java", "motadata/src/main/java/com/mindarray/eventbus/EventBusConstants.java", "motadata/src/main/java/com/mindarray/nms/TopologyEngine.java"]},
    {"id": "fc01bcc7e9ef_compliance_db_refactor", "diff_file": "diff_compliance_db_refactor.patch", "commit_msg": "Rename package from compliance to db", "files": ["motadata/src/main/java/com/mindarray/Bootstrap.java", "motadata/src/main/java/com/mindarray/compliance/ComplianceDBService.java", "motadata/src/main/java/com/mindarray/db/ComplianceDBService.java", "motadata/src/main/java/com/mindarray/db/DBServiceProvider.java"]},
    {"id": "da66bf5d58f0_netroute_manager_removal", "diff_file": "diff_netroute_manager_removal.patch", "commit_msg": "Remove NetRouteManager", "files": ["motadata/src/main/java/com/mindarray/BootstrapPrimary.java", "motadata/src/main/java/com/mindarray/BootstrapStandalone.java", "motadata/src/main/java/com/mindarray/util/MotadataConfigUtil.java"]},
    {"id": "3fa1126b4799_mongodb_protocol_removal", "diff_file": "diff_mongodb_protocol_removal.patch", "commit_msg": "Remove MongoDB protocol support", "files": ["motadata/db-files/dashboard-widgets/mongodb.json", "motadata/src/main/java/com/mindarray/nms/NMSConstants.java", "motadata/src/main/resources/entity-schemas/credential-profiles.json", "motadata/src/main/resources/entity-schemas/templates.json"]},
    {"id": "443c87d78326_polling_failed_template", "diff_file": "diff_polling_failed_template.patch", "commit_msg": "Add polling failed notification template", "files": ["motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java", "motadata/src/main/java/com/mindarray/integration/SlackIntegration.java", "motadata/src/main/java/com/mindarray/integration/TeamsIntegration.java", "motadata/src/main/java/com/mindarray/notification/Notification.java"]},
    {"id": "25441efe4d29_ssh_corner_cases", "diff_file": "diff_ssh_corner_cases.patch", "commit_msg": "Handle SSH corner cases", "files": ["motadata/src/main/java/com/mindarray/config/SSHClientManager.java", "motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java", "motadata/src/test/java/com/mindarray/ssh/TestSSHClientManager.java"]},
]

def load_model():
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True)
    model = PeftModel.from_pretrained(model, LORA_ADAPTER)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    return model, tokenizer

def fetch_rag_context(task: Dict) -> str:
    try:
        query = f"{task['commit_msg']} {' '.join(task['files'][:2])}"
        with httpx.Client(timeout=30.0) as client:
            r = client.post(f"{RAG_URL}/search/hybrid", json={"query": query, "top_k": 3, "include_callers": False, "include_callees": False})
            if r.status_code == 200:
                results = r.json().get("results", [])
                return "\n".join([f"// {x.get('code',x).get('qualified_name','')} ({x.get('code',x).get('file_path','')})" for x in results[:3]])
    except: pass
    return ""

def create_prompt(task: Dict, rag: str = "") -> str:
    files = "\n".join(f"  - {f}" for f in task['files'])
    rag_sec = f"\n## Context\n{rag}\n" if rag else ""
    return f"""You are a Motadata Java developer. Generate unified diff.

## Task: {task['commit_msg']}

## Files to Modify
{files}
{rag_sec}
{FEW_SHOT}
## Instructions
1. Generate diff for EACH file above (exact paths)
2. Use `--- a/` and `+++ b/` prefixes
3. Include `@@ -line,count +line,count @@` headers

Generate diff:
"""

def extract_files(text: str, filter_example: bool = True) -> set:
    files = set()
    for line in text.split('\n'):
        for p in [r'^--- a/(.+)$', r'^\+\+\+ b/(.+)$', r'^diff --git a/(.+?) b/']:
            m = re.match(p, line)
            if m:
                f = m.group(1)
                if not (filter_example and 'example/Example.java' in f):
                    files.add(f)
                break
    return files

def analyze(response: str, expected: str) -> Dict:
    gen_files = extract_files(response, filter_example=True)
    exp_files = extract_files(expected, filter_example=False)
    matched = gen_files & exp_files
    coverage = len(matched) / len(exp_files) if exp_files else 0
    has_hunk = bool(re.search(r'^@@ .+ @@', response, re.MULTILINE))
    has_minus = bool(re.search(r'^--- [ab]/', response, re.MULTILINE))
    has_plus = bool(re.search(r'^\+\+\+ [ab]/', response, re.MULTILINE))
    score = has_minus*0.25 + has_plus*0.25 + has_hunk*0.30 + (len(matched)>0)*0.20
    return {'gen_files': sorted(gen_files), 'exp_files': sorted(exp_files), 'matched': sorted(matched), 'coverage': coverage, 'score': score, 'valid': score >= 0.5}

def similarity(exp: str, gen: str) -> float:
    def changes(t): return {l[1:].strip() for l in t.split('\n') if l.startswith(('+','-')) and not l.startswith(('+++','---'))}
    e, g = changes(exp), changes(gen)
    if not e: return 0
    i = e & g
    p, r = (len(i)/len(g) if g else 0), len(i)/len(e)
    return 2*p*r/(p+r) if p+r else 0

def evaluate_task(model, tokenizer, task: Dict) -> Dict:
    start = time.time()
    rag = fetch_rag_context(task)
    prompt = create_prompt(task, rag)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=2500, temperature=0.7, top_p=0.9, do_sample=True)
    response = tokenizer.decode(out[0], skip_special_tokens=True)
    latency = time.time() - start

    (RESPONSES_DIR / f"{task['id']}.txt").write_text(response)
    expected = (DIFFS_DIR / task['diff_file']).read_text() if (DIFFS_DIR / task['diff_file']).exists() else ""

    analysis = analyze(response, expected)
    sim = similarity(expected, response)
    quality = analysis['score'] * 0.4 + analysis['coverage'] * 0.4 + sim * 0.2

    return {'task_id': task['id'], 'latency_ms': latency*1000, 'rag_context': bool(rag), 'analysis': analysis, 'similarity': sim, 'quality': quality, 'passed': analysis['valid'] and analysis['coverage'] >= 0.5}

def main():
    print("=" * 70)
    print("V16.1 EVALUATION v3 - RAG + Few-shot + Example.java Filter")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Tasks: {len(TASKS)}")
    print("\nImprovements:")
    print("  ✓ Example.java filtered from results")
    print("  ✓ RAG context injection")
    print("  ✓ Few-shot example in prompt")
    print()

    model, tokenizer = load_model()
    print()

    results = []
    for i, task in enumerate(TASKS, 1):
        print(f"[{i}/{len(TASKS)}] {task['id'][:40]}...", end=" ", flush=True)
        r = evaluate_task(model, tokenizer, task)
        results.append(r)
        status = "✅" if r['passed'] else "⚠️"
        print(f"{status} Q={r['quality']:.2f} Cov={r['analysis']['coverage']:.0%} RAG={'Y' if r['rag_context'] else 'N'}")

    # Metrics
    n = len(results)
    metrics = {
        'valid_rate': sum(r['analysis']['valid'] for r in results) / n,
        'avg_coverage': sum(r['analysis']['coverage'] for r in results) / n,
        'avg_similarity': sum(r['similarity'] for r in results) / n,
        'avg_quality': sum(r['quality'] for r in results) / n,
        'pass_rate': sum(r['passed'] for r in results) / n,
        'rag_success_rate': sum(r['rag_context'] for r in results) / n,
    }

    report = {'timestamp': datetime.now().isoformat(), 'version': 'v3_rag_fewshot_filtered', 'total': n, 'metrics': metrics, 'results': results}

    out_file = RESULTS_DIR / "evaluation_v3.json"
    with open(out_file, 'w') as f:
        json.dump(report, f, indent=2)

    print()
    print("=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"Valid Diff Rate:    {metrics['valid_rate']:.1%}")
    print(f"Avg File Coverage:  {metrics['avg_coverage']:.1%}")
    print(f"Avg Similarity:     {metrics['avg_similarity']:.1%}")
    print(f"Avg Quality:        {metrics['avg_quality']:.2f}")
    print(f"Pass Rate:          {metrics['pass_rate']:.1%}")
    print(f"RAG Success Rate:   {metrics['rag_success_rate']:.1%}")
    print("=" * 70)
    print(f"\n📁 Report: {out_file}")
    print(f"📁 Responses: {RESPONSES_DIR}")

if __name__ == "__main__":
    main()

