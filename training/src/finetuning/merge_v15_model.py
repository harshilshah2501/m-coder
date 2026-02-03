#!/usr/bin/env python3
"""
Merge V15 LoRA adapters with base model for deployment.
Output: Full merged model ready for vLLM deployment.
"""

import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# CONFIGURATION
BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
LORA_CHECKPOINT = "training/results/v15_finetuned"
MERGED_OUTPUT = "training/results/v15_merged"


def main():
    print("=" * 80)
    print("🔗 Merging V15 LoRA Adapters with Base Model")
    print("=" * 80)
    print(f"Base Model: {BASE_MODEL_ID}")
    print(f"LoRA Checkpoint: {LORA_CHECKPOINT}")
    print(f"Merged Output: {MERGED_OUTPUT}")
    print("=" * 80)

    # Check checkpoint exists
    checkpoint_path = Path(LORA_CHECKPOINT)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"LoRA checkpoint not found: {LORA_CHECKPOINT}")

    # Load tokenizer
    print("\n🔧 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    print("✅ Tokenizer loaded")

    # Load base model in full precision for merging
    print("\n🔧 Loading base model (this may take a few minutes)...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    print("✅ Base model loaded")

    # Load LoRA adapter
    print("\n🔧 Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, LORA_CHECKPOINT)
    print("✅ LoRA adapter loaded")

    # Merge and unload
    print("\n🔗 Merging adapters with base model...")
    model = model.merge_and_unload()
    print("✅ Merge complete")

    # Save merged model
    print(f"\n💾 Saving merged model to {MERGED_OUTPUT}...")
    model.save_pretrained(MERGED_OUTPUT, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_OUTPUT)
    print("✅ Merged model saved")

    print("\n" + "=" * 80)
    print("✅ V15 MODEL MERGE COMPLETE!")
    print("=" * 80)
    print(f"📁 Output: {MERGED_OUTPUT}")
    print("\n📊 Next steps:")
    print("   1. Deploy with vLLM: ./deploy_v15_vllm.sh")
    print("   2. Test inference: python3 test_v15_model.py")


if __name__ == '__main__':
    main()

