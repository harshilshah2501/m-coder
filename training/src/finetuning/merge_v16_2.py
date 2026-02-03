#!/usr/bin/env python3
"""
V16.2 Model Merge Script
========================
Merges LoRA weights with base model to create final v16.2 model.

After training completes:
1. Load base model (Qwen2.5-Coder-14B-Instruct)
2. Load LoRA adapter from training output
3. Merge weights
4. Save final merged model
"""

import torch
from pathlib import Path
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Configuration
BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-14B-Instruct"
LORA_MODEL_PATH = "/home/harshil/Harshil-PoCs/training/checkpoints/v16_2/checkpoint-1053"
OUTPUT_PATH = "/home/harshil/Harshil-PoCs/models/v16_2/motadata-coder-v16_2-merged"

print("="*80)
print("V16.2 MODEL MERGE")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Base Model: {BASE_MODEL_ID}")
print(f"LoRA Path: {LORA_MODEL_PATH}")
print(f"Output: {OUTPUT_PATH}")
print("="*80)


def main():
    # Verify LoRA model exists
    if not Path(LORA_MODEL_PATH).exists():
        raise FileNotFoundError(f"LoRA model not found at {LORA_MODEL_PATH}")
    
    print("\nSTEP 1: Loading Tokenizer")
    print("-" * 80)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    print("✓ Tokenizer loaded")
    
    print("\nSTEP 2: Loading Base Model")
    print("-" * 80)
    print("Loading in bfloat16...")
    
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    print("✓ Base model loaded")
    
    print("\nSTEP 3: Loading LoRA Adapter")
    print("-" * 80)
    
    model = PeftModel.from_pretrained(base_model, LORA_MODEL_PATH)
    print("✓ LoRA adapter loaded")
    
    print("\nSTEP 4: Merging Weights")
    print("-" * 80)
    
    merged_model = model.merge_and_unload()
    print("✓ Weights merged")
    
    print("\nSTEP 5: Saving Merged Model")
    print("-" * 80)
    
    Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)
    
    merged_model.save_pretrained(OUTPUT_PATH)
    tokenizer.save_pretrained(OUTPUT_PATH)
    
    print(f"✓ Model saved to {OUTPUT_PATH}")
    
    # Calculate model size
    import os
    total_size = 0
    for f in Path(OUTPUT_PATH).rglob("*"):
        if f.is_file():
            total_size += f.stat().st_size
    
    print(f"✓ Total size: {total_size / (1024**3):.2f} GB")
    
    print("\n" + "="*80)
    print("V16.2 MODEL MERGE COMPLETE")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Model Path: {OUTPUT_PATH}")
    print("\nNext Steps:")
    print("1. Update orchestrator to use v16.2 model")
    print("2. Restart vLLM with new model")
    print("3. Run evaluation tests")
    print("="*80)


if __name__ == "__main__":
    main()

