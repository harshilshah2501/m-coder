#!/usr/bin/env python3
"""
MERGING ITER10 - FULL PRECISION
CRITICAL: Load in bfloat16, save in bfloat16 (no quantization conversion)
Based on proven Iter9 merge approach
"""

import torch
from pathlib import Path
from unsloth import FastLanguageModel

def main():
    print("=" * 80)
    print("MERGING ITER10 - FULL PRECISION")
    print("=" * 80)
    
    script_dir = Path(__file__).parent
    checkpoint_dir = script_dir / 'finetuning_output' / 'checkpoint-iter10'
    output_dir = Path('/home/harshil/Harshil-PoCs/motadata-coder-iter10')
    
    print(f"\n📂 Checkpoint: {checkpoint_dir}")
    print(f"📂 Output: {output_dir}")
    
    # Load base model (CRITICAL: Full precision, no quantization)
    print("\n🔧 Loading base model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="/home/harshil/Harshil-PoCs/motadata-coder-iter9",
        max_seq_length=8192,
        dtype=torch.bfloat16,
        load_in_4bit=False,  # ✅ CRITICAL: Full precision
    )
    
    # Prepare for LoRA
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=16,
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing=True,
        use_rslora=False,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    
    # Load trained LoRA weights
    print("📥 Loading LoRA weights...")
    model.load_adapter(str(checkpoint_dir / 'lora_model'))
    
    # Merge and save
    print("🔀 Merging LoRA weights...")
    model = model.merge_and_unload()
    
    print(f"💾 Saving merged model to {output_dir}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(output_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(output_dir))
    
    print("\n✅ Merge complete!")
    print(f"📁 Model: {output_dir}")
    print(f"📊 Size: ~15GB (bfloat16)")
    
    print("\n📝 Next steps:")
    print("  1. Update vLLM to use new model")
    print("  2. Run benchmark: python3 evaluation/run_motadata_bench.py --all")
    print("  3. Compare results with Iter9 baseline")

if __name__ == '__main__':
    main()

