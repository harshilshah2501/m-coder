#!/usr/bin/env python3
"""
Merge v13 LoRA adapter with base model to create full model for deployment.

This script:
1. Loads the base Qwen2.5-Coder-7B-Instruct model
2. Loads the v13 LoRA adapter
3. Merges them into a single model
4. Saves the merged model for vLLM deployment

Usage:
    python3 evaluation/finetuning/merge_v13.py
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os
from pathlib import Path

# Configuration
BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
LORA_ADAPTER_PATH = "./finetuning_output/motadata-coder-v13"
OUTPUT_PATH = "./finetuning_output/motadata-coder-v13-merged"

def main():
    print("=" * 80)
    print("🔀 MERGING V13 LORA ADAPTER WITH BASE MODEL")
    print("=" * 80)
    print(f"Base Model: {BASE_MODEL_ID}")
    print(f"LoRA Adapter: {LORA_ADAPTER_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 80)
    print()
    
    # Check if adapter exists
    if not os.path.exists(LORA_ADAPTER_PATH):
        print(f"❌ Error: LoRA adapter not found at {LORA_ADAPTER_PATH}")
        return
    
    # Load tokenizer
    print("📝 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        LORA_ADAPTER_PATH,
        trust_remote_code=True
    )
    print("✅ Tokenizer loaded")
    print()
    
    # Load base model
    print("🔧 Loading base model...")
    print("   (This may take a few minutes...)")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    print("✅ Base model loaded")
    print()
    
    # Load LoRA adapter
    print("🔧 Loading LoRA adapter...")
    model = PeftModel.from_pretrained(
        base_model,
        LORA_ADAPTER_PATH,
        torch_dtype=torch.bfloat16
    )
    print("✅ LoRA adapter loaded")
    print()
    
    # Merge LoRA weights into base model
    print("🔀 Merging LoRA weights into base model...")
    print("   (This may take a few minutes...)")
    merged_model = model.merge_and_unload()
    print("✅ Merge complete!")
    print()
    
    # Save merged model
    print(f"💾 Saving merged model to {OUTPUT_PATH}...")
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    merged_model.save_pretrained(
        OUTPUT_PATH,
        safe_serialization=True,
        max_shard_size="5GB"
    )
    print("✅ Model saved")
    print()
    
    # Save tokenizer
    print("💾 Saving tokenizer...")
    tokenizer.save_pretrained(OUTPUT_PATH)
    print("✅ Tokenizer saved")
    print()
    
    # Get model size
    model_size = sum(os.path.getsize(os.path.join(OUTPUT_PATH, f)) 
                     for f in os.listdir(OUTPUT_PATH) 
                     if os.path.isfile(os.path.join(OUTPUT_PATH, f)))
    model_size_gb = model_size / (1024**3)
    
    print("=" * 80)
    print("✅ MERGE COMPLETE!")
    print("=" * 80)
    print(f"📁 Merged model: {OUTPUT_PATH}")
    print(f"💾 Size: {model_size_gb:.2f} GB")
    print()
    print("🚀 Next steps:")
    print("   1. Test the merged model:")
    print(f"      python3 evaluation/test_model.py --model {OUTPUT_PATH}")
    print()
    print("   2. Run benchmark:")
    print(f"      python3 evaluation/run_benchmark.py --model {OUTPUT_PATH}")
    print()
    print("   3. Deploy with vLLM:")
    print(f"      vllm serve {OUTPUT_PATH} --port 8000")
    print("=" * 80)

if __name__ == "__main__":
    main()

