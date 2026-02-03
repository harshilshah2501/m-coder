import json

FILE = "/home/harshil/Harshil-PoCs/RAG-Datastore/training-artifacts/benchmark_jira.jsonl"

def is_good(desc):
    if len(desc) < 30: return False
    desc_lower = desc.lower().strip()
    bad_phrases = ["code refactor", "refactoring", "changes", "update", "fix bug", "bug fix", "comments added"]
    if desc_lower in bad_phrases: return False
    return True

total = 0
good = 0
has_fields = 0

with open(FILE, 'r') as f:
    for line in f:
        total += 1
        try:
            data = json.loads(line)
            desc = data.get("task_description", "")
            
            # check fields
            files = data.get("files", [])
            if not files: continue
            f0 = files[0]
            if "path" not in f0 or "content_before" not in f0 or "expected_diff" not in f0:
                continue
            has_fields += 1
            
            if is_good(desc):
                good += 1
        except: pass

print(f"Total: {total}")
print(f"Has Valid Fields: {has_fields}")
print(f"Good Description (>30 chars): {good}")
print(f"Salvage Ratio: {int(good/total*100)}%")
