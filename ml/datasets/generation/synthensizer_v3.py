import json
import logging
from vllm import LLM, SamplingParams
import os

# CONFIG
INPUT_FILE = "/home/harshil/Harshil-PoCs/Dataset-Generation/enriched_production_prs.jsonl"
OUTPUT_FILE = "/home/harshil/Harshil-PoCs/Dataset-Generation/enriched_with_reasoning.jsonl"
MODEL_PATH = "Qwen/Qwen2.5-Coder-32B-Instruct" # Ensure this path is correct on H100

def synthesize():
    logging.basicConfig(level=logging.INFO)
    
    if not os.path.exists(INPUT_FILE):
        logging.error(f"File not found: {INPUT_FILE}")
        return

    # 1. Load Data
    logging.info(f"Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r') as f:
        data = [json.loads(line) for line in f]
    
    logging.info(f"Loaded {len(data)} commits. Preparing prompts...")

    # 2. Build Prompts
    prompts = []
    valid_indices = []

    for i, entry in enumerate(data):
        instruction = entry.get('instruction', '')
        files = entry.get('files', [])
        
        # Heuristic: Use the diff of the first file to generate the plan
        # (Reasoning usually applies to the whole PR, not just file-by-file)
        if not files: 
            continue
            
        diff_context = files[0].get('diff', '')[:6000] # Fit in context
        
        prompt = f"""<|im_start|>system
You are a Senior Software Architect. Analyze the instruction and the code diff. 
Explain the reasoning for this change.
<|im_end|>
<|im_start|>user
Instruction: {instruction}

Diff:
{diff_context}

Provide a concise, step-by-step implementation plan and reasoning. Start with "Here is the plan:".
<|im_end|>
<|im_start|>assistant
"""
        prompts.append(prompt)
        valid_indices.append(i)

    # 3. Generate with vLLM
    logging.info(f"Starting vLLM Inference on {len(prompts)} items...")
    
    # Adjust tensor_parallel_size if using multiple GPUs (e.g., 2, 4, 8)
    llm = LLM(model=MODEL_PATH, tensor_parallel_size=1) 
    
    params = SamplingParams(temperature=0.7, max_tokens=512)
    outputs = llm.generate(prompts, params)

    # 4. Save Results
    logging.info("Saving results...")
    with open(OUTPUT_FILE, 'w') as f:
        for j, output in enumerate(outputs):
            original_idx = valid_indices[j]
            entry = data[original_idx]
            
            # Inject Reasoning
            entry['reasoning'] = output.outputs[0].text.strip()
            
            f.write(json.dumps(entry) + "\n")

    logging.info(f"Done! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    synthesize()
