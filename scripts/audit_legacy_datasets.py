import json
import os
from pathlib import Path

# The Gold Standard to verify against
GOLD_FILE = "/home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning/motadata_finetuning_data.jsonl"

# The 16 files to inspect
FILES_TO_CHECK = [
    "/home/harshil/Harshil-PoCs/Finetuning/full_training_train.jsonl",
    "/home/harshil/Harshil-PoCs/Finetuning/full_training_test.jsonl",
    "/home/harshil/Harshil-PoCs/Finetuning/full_training_data_shuffled.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/enriched_production_prs.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/dataset_a_architecture.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/dataset_a_enhanced.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/full_training_data.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/final_training_set_reasoning.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/full_training_data_shuffled.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/dataset_c_hybrid.jsonl",
    "/home/harshil/Harshil-PoCs/Dataset-Generation/dataset_review.jsonl",
    "/home/harshil/Harshil-PoCs/Iter10-Training/val.jsonl",
    "/home/harshil/Harshil-PoCs/Iter10-Training/train.jsonl",
    "/home/harshil/Harshil-PoCs/Iter11-Training/val.jsonl",
    "/home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning/finetuning_output/val.jsonl",
    "/home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning/finetuning_output/train.jsonl"
]

# 1. Load Gold Hashes
gold_hashes = set()
try:
    with open(GOLD_FILE, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                # Hash user content + assistant content to detect duplicates
                msgs = data.get("messages", [])
                content = "".join([m.get("content", "") for m in msgs])
                gold_hashes.add(hash(content))
            except: pass
except Exception as e:
    print(f"Warning: Could not load Gold file: {e}")

print(f"{'FILE':<55} | {'COUNT':<6} | {'DUP%':<4} | {'LAZY%':<5} | {'SYS_PROMPT'}")
print("-" * 105)

for filepath in FILES_TO_CHECK:
    path = Path(filepath)
    if not path.exists():
        print(f"{path.name:<55} | MISSING")
        continue

    total = 0
    dups = 0
    lazy = 0
    system_prompts = set()
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if not line.strip(): continue
                total += 1
                try:
                    data = json.loads(line)
                    
                    # 1. Check Duplication
                    msgs = data.get("messages", [])
                    if not msgs and "prompt" in data: # Instruct format
                         content = data.get("prompt", "") + data.get("completion", "")
                    else:
                         content = "".join([m.get("content", "") for m in msgs])
                    
                    if hash(content) in gold_hashes:
                        dups += 1
                        
                    # 2. Check Lazy
                    user_msgs = [m for m in msgs if m.get('role') == 'user']
                    if user_msgs:
                        if len(user_msgs[0].get('content', '')) < 20:
                            lazy += 1
                            
                    # 3. Check System Prompt
                    if msgs and msgs[0].get('role') == 'system':
                        system_prompts.add(msgs[0]['content'][:20]) # First 20 chars
                    else:
                        system_prompts.add("NONE")
                        
                except:
                    pass
    except Exception as e:
        print(f"{path.name:<55} | ERROR: {e}")
        continue
        
    dup_pct = int(dups/total*100) if total else 0
    lazy_pct = int(lazy/total*100) if total else 0
    sys_status = "NONE"
    if len(system_prompts) == 1:
        sys_status = list(system_prompts)[0].replace("\n", "")
    elif len(system_prompts) > 1:
        sys_status = "MIXED"
    
    print(f"{path.name:<55} | {total:<6} | {dup_pct}%   | {lazy_pct}%    | {sys_status}")
