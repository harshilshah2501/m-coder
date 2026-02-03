import json
import random

FILE = "/home/harshil/Harshil-PoCs/RAG-Datastore/training-artifacts/benchmark_jira.jsonl"

print(f"Sampling {FILE}...")
with open(FILE, 'r') as f:
    lines = f.readlines()
    
samples = random.sample(lines, 5)

for i, line in enumerate(samples):
    data = json.loads(line)
    print(f"\n[Example {i+1}]")
    print(f"Description: {data.get('task_description', 'N/A')}")
    print(f"Description Len: {len(data.get('task_description', ''))}")
    
    files = data.get("files", [])
    for j, fobj in enumerate(files):
        print(f"  File {j+1} Path: {fobj.get('file_path', 'MISSING')}")
        diff = fobj.get("expected_diff", "")
        print(f"  Diff Start: {diff[:50].replace(chr(10), ' ')}...")
        print(f"  Has Headers? {'--- a/' in diff}")
