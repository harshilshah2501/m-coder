#!/usr/bin/env python3
"""
Merge V14 LoRA adapters with base model for deployment.
"""

import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Paths
BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
LORA_CHECKPOINT = "./finetuning_output/motadata-coder-v14"
OUTPUT_DIR = "./finetuning_output/motadata-coder-v14-merged"

def main():
    print("=" * 80)
    print("🔗 MERGING V14 LORA ADAPTERS WITH BASE MODEL")
    print("=" * 80)
    print(f"\n📂 Base Model: {BASE_MODEL_ID}")
    print(f"📂 LoRA Checkpoint: {LORA_CHECKPOINT}")
    print(f"📂 Output: {OUTPUT_DIR}")
    print()
    
    # Check if LoRA checkpoint exists
    lora_path = Path(LORA_CHECKPOINT)
    if not lora_path.exists():
        print(f"❌ LoRA checkpoint not found at {LORA_CHECKPOINT}")
        return 1
    
    # Load tokenizer
    print("🔧 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    print("✅ Tokenizer loaded")
    
    # Load base model
    print("\n🔧 Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    print("✅ Base model loaded")
    
    # Load LoRA adapters
    print("\n🔧 Loading LoRA adapters...")
    model = PeftModel.from_pretrained(base_model, LORA_CHECKPOINT)
    print("✅ LoRA adapters loaded")
    
    # Merge adapters
    print("\n🔗 Merging LoRA adapters with base model...")
    merged_model = model.merge_and_unload()
    print("✅ Merge complete")
    
    # Save merged model
    print(f"\n💾 Saving merged model to {OUTPUT_DIR}...")
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    merged_model.save_pretrained(
        OUTPUT_DIR,
        safe_serialization=True,
        max_shard_size="5GB"
    )
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("✅ Merged model saved")
    
    # Verify
    print("\n✅ Verification:")
    print(f"   Model files: {list(output_path.glob('*.safetensors'))[:3]}")
    print(f"   Tokenizer files: {list(output_path.glob('tokenizer*'))}")
    
    print("\n" + "=" * 80)
    print("✅ MERGE COMPLETE!")
    print("=" * 80)
    print(f"\n📁 Merged model ready at: {OUTPUT_DIR}")
    print("\n📊 Next steps:")
    print("   1. Deploy with vLLM")
    print("   2. Test on multi-file tasks")
    print("   3. Compare with v13 baseline")
    print()
    
    return 0

if __name__ == '__main__':
    exit(main())

