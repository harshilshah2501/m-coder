import json
import os
from collections import Counter
import statistics
from pathlib import Path

# All identified files
FILES = [
    "/home/harshil/Harshil-PoCs/RAG-Datastore/training-artifacts/benchmark_jira.jsonl",
    "/home/harshil/Harshil-PoCs/RAG-Datastore/training-artifacts/motadata_bench_corrections.jsonl",
    "/home/harshil/Harshil-PoCs/RAG-Datastore/training-artifacts/dataset_b_multifile.jsonl",
    "/home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning/motadata_finetuning_data.jsonl",
    "/home/harshil/Harshil-PoCs/Iter10-Training/train.jsonl",
    "/home/harshil/Harshil-PoCs/Iter11-Training/train.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/dataset_a_enhanced.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/dataset_a_architecture.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/dataset_c_hybrid.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/dataset_c_reasoning.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/final_training_set_reasoning.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/enriched_production_prs.jsonl",
]

def analyze_file(filepath):
    path = Path(filepath)
    if not path.exists():
        return None

    stats = {
        "filename": path.name,
        "path": str(path),
        "total": 0,
        "format": "unknown",
        "has_system_prompt": 0,
        "avg_user_prompt_len": 0,
        "lazy_prompts": 0, # < 20 chars
        "unique_system_prompts": set(),
        "example_lazy_prompt": None
    }
    
    user_prompt_lens = []

    try:
        with open(filepath, 'r') as f:
            for line in f:
                if not line.strip(): continue
                stats["total"] += 1
                try:
                    data = json.loads(line)
                    
                    # Detect Format
                    if "messages" in data:
                        stats["format"] = "chat"
                        msgs = data["messages"]
                        
                        # Check System Prompt
                        if msgs and msgs[0]['role'] == 'system':
                            stats["has_system_prompt"] += 1
                            stats["unique_system_prompts"].add(msgs[0]['content'][:50]) # Store prefix
                        
                        # Check User Prompt
                        user_msgs = [m for m in msgs if m['role'] == 'user']
                        if user_msgs:
                            content = user_msgs[0]['content']
                            l = len(content)
                            user_prompt_lens.append(l)
                            if l < 20:
                                stats["lazy_prompts"] += 1
                                if not stats["example_lazy_prompt"]:
                                    stats["example_lazy_prompt"] = content

                    elif "task_description" in data:
                        stats["format"] = "raw_jira"
                        l = len(data.get("task_description", ""))
                        user_prompt_lens.append(l)

                    elif "instruction" in data: # Alpaca style
                        stats["format"] = "instruct"

                except:
                    pass
        
        if user_prompt_lens:
            stats["avg_user_prompt_len"] = int(statistics.mean(user_prompt_lens))
        
        stats["unique_system_prompts"] = list(stats["unique_system_prompts"])
        return stats

    except Exception as e:
        return {"filename": path.name, "error": str(e)}

print(f"{'FILENAME':<45} | {'FMT':<8} | {'CNT':<5} | {'SYS%':<4} | {'LAZY':<4} | {'NOTES'}")
print("-" * 120)

for f in FILES:
    res = analyze_file(f)
    if not res or "error" in res:
        print(f"{Path(f).name:<45} | ERROR")
        continue
        
    sys_pct = int((res['has_system_prompt'] / res['total']) * 100) if res['total'] > 0 else 0
    lazy_pct = int((res['lazy_prompts'] / res['total']) * 100) if res['total'] > 0 else 0
    
    note = ""
    if len(res['unique_system_prompts']) > 1:
        note += "Mixed Sys Prompts. "
    if res['example_lazy_prompt']:
        note += f"Ex lazy: '{res['example_lazy_prompt'][:20]}'"
        
    print(f"{res['filename']:<45} | {res['format']:<8} | {res['total']:<5} | {sys_pct}%  | {lazy_pct}%   | {note}")
