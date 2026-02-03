import json
import random

GOLD_FILE = "/home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning/motadata_finetuning_data.jsonl"
JIRA_FILE = "/home/harshil/Harshil-PoCs/RAG-Datastore/training-artifacts/benchmark_jira.jsonl"
OUTPUT_FILE = "/home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning/v12_combined.jsonl"

SYSTEM_PROMPT = """You are Motadata Coder, a helpful AI assistant for the Motadata codebase.
Follow these guidelines:
1. Use relative file paths.
2. Do not include copyright headers.
3. Output tool calls as valid JSON: {"tool_calls": [{"name": "tool_name", "arguments": {...}}]}
4. When editing code, ALWAYS use unified diff format:
```diff
--- a/path/to/file
+++ b/path/to/file
@@ ... @@
- old
+ new
```
"""

TOTAL_WRITTEN = 0
STATS = {"gold": 0, "jira_chat": 0, "jira_tool": 0}

def is_valid_jira(data):
    desc = data.get("task_description", "")
    if len(desc) < 30: return False
    bad = ["code refactor", "refactoring", "update", "fix bug", "changes"]
    if desc.lower().strip() in bad: return False
    
    files = data.get("files", [])
    if not files: return False
    f0 = files[0]
    if "path" not in f0 or "content_before" not in f0 or "expected_diff" not in f0:
        return False
    return True

print("Generating v12_combined.jsonl...")

with open(OUTPUT_FILE, 'w') as out:
    # 1. Process Gold Data
    print("Processing Gold Data...")
    with open(GOLD_FILE, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                # Overwrite system prompt to ensure consistency? 
                # Actually Gold data has specific prompts. Let's trust Gold for now, 
                # BUT maybe unifying system prompt is better?
                # Let's keep Gold as is (it's verified).
                out.write(json.dumps(data) + "\n")
                STATS["gold"] += 1
                TOTAL_WRITTEN += 1
            except: pass

    # 2. Process JIRA Data
    print("Processing JIRA Data...")
    with open(JIRA_FILE, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if not is_valid_jira(data): continue
                
                desc = data["task_description"]
                f_obj = data["files"][0]
                path = f_obj["path"]
                content = f_obj["content_before"]
                diff = f_obj["expected_diff"]
                
                # A. Tool Trace Example (Type-C)
                # Teach the model to: Search -> Read -> Diff
                tool_msg_assistant = {
                    "role": "assistant",
                    "content": f"<thought>I need to find the file relevant to '{desc}'. Based on general knowledge, I'll search for it.</thought>\n" +
                               json.dumps({
                                   "tool_calls": [{
                                       "name": "read_file",
                                       "arguments": {"path": path}
                                   }]
                               })
                }
                tool_msg_tool = {
                    "role": "tool",
                    "content": f"File Content: {path}\n\n{content}"
                }
                final_response = {
                    "role": "assistant",
                    "content": f"<thought>I have read the file. Now I will generate the diff to implement: {desc}</thought>\nEveryone uses unified diffs.\n\n```diff\n{diff}\n```"
                }

                tool_example = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": desc},
                        tool_msg_assistant,
                        tool_msg_tool,
                        final_response
                    ]
                }
                out.write(json.dumps(tool_example) + "\n")
                STATS["jira_tool"] += 1
                TOTAL_WRITTEN += 1

                # B. Direct Chat Example (Type-B)
                # Standard Context -> Diff
                direct_example = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"File: {path}\nContent:\n{content}\n\nTask: {desc}"},
                        {"role": "assistant", "content": f"```diff\n{diff}\n```"}
                    ]
                }
                out.write(json.dumps(direct_example) + "\n")
                STATS["jira_chat"] += 1
                TOTAL_WRITTEN += 1
                
            except Exception as e:
                pass

print(f"\nDone! Total Written: {TOTAL_WRITTEN}")
print(f"Stats: {STATS}")
