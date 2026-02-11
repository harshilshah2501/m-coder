#!/usr/bin/env python3
"""
Merge LoRA Adapter with Base Model - V16.1
==========================================
Merges the trained LoRA adapter (49MB) with Qwen2.5-Coder-14B base model.

This creates a single, deployable model without needing to load adapters separately.
Uses bfloat16 throughout to avoid the 4-bit corruption issue from Iteration 9.
"""

import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# CONFIGURATION
BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-14B-Instruct"
ADAPTER_PATH = "/home/harshil/Harshil-PoCs/models/v16_1_finetuned"
OUTPUT_PATH = "/home/harshil/Harshil-PoCs/models/v16_1_merged"

print("=" * 80)
print("V16.1 LORA MERGE - Clean bfloat16 Merge")
print("=" * 80)
print(f"Base Model: {BASE_MODEL_ID}")
print(f"LoRA Adapter: {ADAPTER_PATH}")
print(f"Output: {OUTPUT_PATH}")
print("=" * 80)

# Step 1: Load base model in bfloat16
print("\n[1/4] Loading base model (bfloat16)...")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)
print("   ✓ Base model loaded")

# Step 2: Load LoRA adapter
print("\n[2/4] Loading LoRA adapter...")
model = PeftModel.from_pretrained(
    base_model,
    ADAPTER_PATH,
    torch_dtype=torch.bfloat16
)
print("   ✓ LoRA adapter loaded")

# Step 3: Merge adapter into base model
print("\n[3/4] Merging LoRA weights into base model...")
print("   This may take a few minutes...")
merged_model = model.merge_and_unload()
print("   ✓ Merge complete!")

# Step 4: Save merged model
print("\n[4/4] Saving merged model...")
Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

merged_model.save_pretrained(
    OUTPUT_PATH,
    safe_serialization=True,
    max_shard_size="5GB"
)

# Also save tokenizer
print("   Saving tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
tokenizer.save_pretrained(OUTPUT_PATH)

print("\n" + "=" * 80)
print("✅ MERGE COMPLETE!")
print("=" * 80)
print(f"Merged model saved to: {OUTPUT_PATH}")
print("\nModel is ready for:")
print("  - Direct inference")
print("  - vLLM deployment")
print("  - Production use")
print("\nNo adapter loading needed - this is a standalone model!")
print("=" * 80)

