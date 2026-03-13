import json
import os
import logging

logging.basicConfig(level=logging.INFO)

# Input comes from the SYNTHESIZER now
INPUT_FILE = "enriched_with_reasoning.jsonl" 
OUTPUT_FILE = "final_training_set_reasoning.jsonl"
SYSTEM_PROMPT = "You are a Senior Software Engineer at Motadata. Implement the requested changes."

def build_reasoning_dataset():
    if not os.path.exists(INPUT_FILE):
        logging.error(f"Input file {INPUT_FILE} not found. Did you run synthesis?")
        return

    samples = []
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                commit = json.loads(line)
                instruction = commit.get('instruction', '').strip()
                reasoning = commit.get('reasoning', '').strip()
                
                files = commit.get('files', [])
                
                for file in files:
                    path = file.get('path', 'unknown')
                    src = file.get('source_before', '')
                    diff = file.get('diff', '')
                    is_new = file.get('is_new_file', False)
                    
                    if not diff: continue
                    
                    # Context Slicing (Simple Top 800 lines)
                    if is_new or not src:
                        smart_source = "// New File"
                    else:
                        lines = src.split('\n')
                        if len(lines) > 800:
                            smart_source = "\n".join(lines[:800]) + "\n// ... truncated ..."
                        else:
                            smart_source = src

                    # --- THE KEY CHANGE IS HERE ---
                    user_content = f"File: `{path}`\n\n``````\n\nInstruction: {instruction}"
                    
                    # Assistant output includes REASONING (if available) + DIFF
                    if reasoning:
                        assistant_content = f"{reasoning}\n\n``````"
                    else:
                        # Fallback if synthesis failed for this sample
                        assistant_content = f"``````"
                    # ------------------------------
                    
                    samples.append({
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_content},
                            {"role": "assistant", "content": assistant_content}
                        ],
                        "metadata": {"source": "git_pr_reasoning", "hash": commit.get('hash')}
                    })

            except Exception as e:
                logging.error(f"Builder error: {e}")
                continue

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")

    logging.info(f"Reasoning Build Complete. Total Samples: {len(samples)}")

if __name__ == "__main__":
    build_reasoning_dataset()
