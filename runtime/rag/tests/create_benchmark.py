import json
import os

INPUT_FILE = '/home/harshil/Harshil-PoCs/Dataset-Generation/enriched_production_prs.jsonl'
OUTPUT_FILE = '/home/harshil/Harshil-PoCs/RAG-Datastore/benchmark_jira.jsonl'

def process_dataset():
    print(f"Processing {INPUT_FILE}...")
    count = 0
    with open(INPUT_FILE, 'r') as infile, open(OUTPUT_FILE, 'w') as outfile:
        for line in infile:
            try:
                data = json.loads(line)
                
                # Basic validation
                if not data.get('instruction'):
                    continue
                if not data.get('files'):
                    continue
                
                # Construct benchmark entry
                entry = {
                    "id": data.get('hash'),
                    "task_description": data.get('instruction'),
                    "files": []
                }
                
                valid_entry = True
                for f in data['files']:
                    # We need source_before to be able to simulate the task
                    # If it's a new file, source_before might be null or empty, which is fine (agent creates file)
                    # But if it's a modification, we need source_before.
                    
                    if not f.get('is_new_file') and f.get('source_before') is None:
                        # Skip if we don't have the starting state for a modified file
                        # valid_entry = False
                        # break
                        # Actually, let's just include what we have, maybe the agent can infer or we skip this file?
                        # For a rigorous benchmark, we should probably skip this file or the whole entry.
                        # Let's skip the file for now, but if no files remain, skip entry.
                        continue

                    file_entry = {
                        "path": f.get('path'),
                        "language": "java" if f.get('path', '').endswith('.java') else "text",
                        "change_type": "ADD" if f.get('is_new_file') else "MODIFY",
                        "content_before": f.get('source_before') or "",
                        "expected_diff": f.get('diff')
                    }
                    entry['files'].append(file_entry)
                
                if not entry['files']:
                    continue
                    
                outfile.write(json.dumps(entry) + '\n')
                count += 1
                
            except json.JSONDecodeError:
                print("Skipping invalid JSON line")
                continue
                
    print(f"Created {OUTPUT_FILE} with {count} benchmark entries.")

if __name__ == "__main__":
    process_dataset()
