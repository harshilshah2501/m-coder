import json
import statistics
from pathlib import Path

FILE_JIRA = "/home/harshil/Harshil-PoCs/RAG-Datastore/training-artifacts/benchmark_jira.jsonl"
FILE_GOLD = "/home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning/motadata_finetuning_data.jsonl"

def analyze_dataset(filepath, format_type):
    print(f"Analyzing {Path(filepath).name}...")
    lengths = []
    diff_stats = {"total": 0, "valid": 0}
    
    with open(filepath, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                
                # Length Check
                if format_type == "jira":
                    text = data.get("task_description", "")
                    diffs = [f.get("expected_diff", "") for f in data.get("files", [])]
                else: # chat
                    msgs = data.get("messages", [])
                    user_msgs = [m for m in msgs if m['role'] == "user"]
                    text = user_msgs[0]['content'] if user_msgs else ""
                    # Diff check for chat is harder, skip for now or parse content
                    assistant_msgs = [m for m in msgs if m['role'] == "assistant"]
                    diffs = [m['content'] for m in assistant_msgs]

                lengths.append(len(text))
                
                # Diff Check
                for diff in diffs:
                    diff_stats["total"] += 1
                    if "--- a/" in diff and "+++ b/" in diff and "@@" in diff:
                        diff_stats["valid"] += 1
                        
            except: pass
            
    return lengths, diff_stats

len_jira, diffs_jira = analyze_dataset(FILE_JIRA, "jira")
len_gold, diffs_gold = analyze_dataset(FILE_GOLD, "chat")

print("\n=== HEAD-TO-HEAD COMPARISON ===")
print(f"{'Metric':<20} | {'JIRA (Raw)':<20} | {'GOLD (Chat)':<20}")
print("-" * 66)
print(f"{'Count':<20} | {len(len_jira):<20} | {len(len_gold):<20}")

avg_jira = int(statistics.mean(len_jira)) if len_jira else 0
avg_gold = int(statistics.mean(len_gold)) if len_gold else 0
print(f"{'Avg Content Len':<20} | {avg_jira:<20} | {avg_gold:<20}")

valid_jira = int(diffs_jira['valid']/diffs_jira['total']*100) if diffs_jira['total'] else 0
valid_gold = int(diffs_gold['valid']/diffs_gold['total']*100) if diffs_gold['total'] else 0
print(f"{'Valid Diffs %':<20} | {valid_jira}%{'':<19} | {valid_gold}%{'':<19}")

print("\n--- CONCLUSION ---")
if avg_jira > avg_gold * 0.5: # If JIRA is at least half as rich as Gold (Gold includes file content in prompt, JIRA description is just task)
    # Wait, Gold user prompt includes FILE CONTENT. JIRA Description is just the task.
    # So JIRA length will naturally be smaller. 
    # But JIRA *has* file content in separate field.
    print("JIRA task descriptions are separate from file content.")
    print(f"JIRA Avg Description: {avg_jira} chars (pure instruction)")
    # Let's check JIRA Task vs Gold Instruction (hard to separate in Gold)
    
print(f"JIRA Diff Validity: {valid_jira}%")
if valid_jira > 95:
    print("EXCELLENT: JIRA contains valid diffs ready for training.")
elif valid_jira > 80:
    print("GOOD: JIRA diffs are mostly valid.")
else:
    print("WARNING: JIRA diffs need cleaning.")
