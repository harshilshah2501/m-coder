#!/usr/bin/env python3
"""
Merge v12 LoRA adapter with base model
Creates a standalone merged model for vLLM deployment
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from pathlib import Path

def main():
    print("=" * 80)
    print("MERGING V12 LORA ADAPTER")
    print("=" * 80)
    
    base_model_name = "Qwen/Qwen2.5-Coder-7B-Instruct"
    adapter_path = "/home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning/finetuning_output/motadata-coder-v12"
    output_path = "/home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning/finetuning_output/motadata-coder-v12-merged"
    
    print(f"\n📂 Base model: {base_model_name}")
    print(f"📂 LoRA adapter: {adapter_path}")
    print(f"📂 Output: {output_path}")
    
    # Load base model
    print("\n🔧 Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    print("✅ Base model loaded")
    
    # Load LoRA adapter
    print("\n🔧 Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    print("✅ LoRA adapter loaded")
    
    # Merge
    print("\n🔀 Merging LoRA weights into base model...")
    merged_model = model.merge_and_unload()
    print("✅ Merge complete")
    
    # Load tokenizer
    print("\n🔧 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(adapter_path)
    print("✅ Tokenizer loaded")
    
    # Save merged model
    print(f"\n💾 Saving merged model to {output_path}...")
    Path(output_path).mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(output_path, safe_serialization=True)
    tokenizer.save_pretrained(output_path)
    print("✅ Merged model saved")
    
    print("\n" + "=" * 80)
    print("✅ MERGE COMPLETE!")
    print("=" * 80)
    print(f"\n📁 Merged model location: {output_path}")
    print(f"📊 Size: ~15GB (bfloat16)")
    
    print("\n📝 Next steps:")
    print("  1. Update vLLM service to use merged model:")
    print(f"     --model {output_path}")
    print("  2. Remove --enable-lora and --lora-modules flags")
    print("  3. Restart service: sudo systemctl restart motadata-coder")
    print("  4. Test the model")

if __name__ == '__main__':
    main()

