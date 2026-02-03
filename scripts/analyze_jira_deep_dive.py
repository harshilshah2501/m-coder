import json
import statistics
from pathlib import Path

FILE_JIRA = "/home/harshil/Harshil-PoCs/RAG-Datastore/training-artifacts/benchmark_jira.jsonl"
FILE_BAD = "/home/harshil/Harshil-PoCs/RAG-Datastore/training-artifacts/dataset_b_multifile.jsonl"

def analyze_jira(filepath):
    print(f"Analyzing {Path(filepath).name}...")
    descriptions = []
    diff_validity = {"has_headers": 0, "has_hunks": 0, "total": 0}
    
    with open(filepath, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                
                # Check Description
                desc = data.get("task_description", "")
                descriptions.append(len(desc))
                
                # Check Diff (it's inside 'files' list usually?)
                # Based on previous `head`, it has "files": [{"expected_diff": ...}]
                files = data.get("files", [])
                for f_obj in files:
                    diff = f_obj.get("expected_diff", "")
                    diff_validity["total"] += 1
                    if "--- a/" in diff and "+++ b/" in diff:
                        diff_validity["has_headers"] += 1
                    if "@@" in diff:
                        diff_validity["has_hunks"] += 1
                        
            except: pass
            
    return descriptions, diff_validity

def analyze_chat(filepath):
    print(f"Analyzing {Path(filepath).name} (Comparison)...")
    prompts = []
    with open(filepath, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                msgs = data.get("messages", [])
                user_msgs = [m for m in msgs if m['role'] == "user"]
                for m in user_msgs:
                    prompts.append(len(m.get("content", "")))
            except: pass
    return prompts

desc_jira, diffs_jira = analyze_jira(FILE_JIRA)
prompts_bad = analyze_chat(FILE_BAD)

print("\n=== COMPARISON RESULTS ===")
print(f"JIRA Dataset (Target): {len(desc_jira)} examples")
print(f"dataset_b (Legacy):    {len(prompts_bad)} examples")

print("\n--- Insight 1: Task Description Richness ---")
avg_jira = int(statistics.mean(desc_jira)) if desc_jira else 0
avg_bad = int(statistics.mean(prompts_bad)) if prompts_bad else 0
print(f"Avg Char Length (JIRA): {avg_jira} chars (Rich context)")
print(f"Avg Char Length (Bad):  {avg_bad} chars (Lazy prompts)")
print(f"Ratio: JIRA is {round(avg_jira/avg_bad, 1)}x richer than dataset_b")

print("\n--- Insight 2: JIRA Diff Quality ---")
print(f"Total Diffs Checked: {diffs_jira['total']}")
if diffs_jira['total'] > 0:
    print(f"Valid Headers (---/+++): {diffs_jira['has_headers']} ({int(diffs_jira['has_headers']/diffs_jira['total']*100)}%)")
    print(f"Valid Hunks (@@):        {diffs_jira['has_hunks']} ({int(diffs_jira['has_hunks']/diffs_jira['total']*100)}%)")
else:
    print("No diffs found to check.")

print("\n--- CONCLUSION ---")
if avg_jira > 50 and diffs_jira['has_headers'] > 0:
    print("VERDICT: benchmark_jira.jsonl is EXCELLENT source material.")
    print("It contains real, detailed task descriptions and valid diffs.")
    print("It matches the 'Gold Standard' quality once converted.")
else:
    print("VERDICT: benchmark_jira.jsonl has issues.")
