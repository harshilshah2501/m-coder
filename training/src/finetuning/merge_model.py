from unsloth import FastLanguageModel
import os
import sys

# --- CONFIG ---
ADAPTER_DIR = "/home/harshil/Harshil-PoCs/Finetuning/training_outputs/h100_run/lora_model"
# 1. We rename the output folder to 'motadata-coder' here
OUTPUT_DIR = "/home/harshil/Harshil-PoCs/Finetuning/merged_models/motadata-coder" 

def print_now(msg):
    print(msg, flush=True)

if __name__ == "__main__":
    print_now("="*50)
    print_now(f"🚀 Starting Merge Process")
    print_now(f"   Source: {ADAPTER_DIR}")
    print_now(f"   Target: {OUTPUT_DIR}")
    print_now("="*50)

    # 1. Load the Adapter
    # This can take 10-30 seconds depending on disk speed
    print_now("⏳ Loading base model and adapters (this may take a moment)...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        ADAPTER_DIR,
        max_seq_length = 16384,
        dtype = None,
        load_in_4bit = False,
    )
    print_now("✅ Model loaded successfully.")

    # 2. Merge and Save
    # This writes ~14GB to disk. It can take 2-5 minutes.
    print_now(f"💾 Merging to 16-bit (BFloat16) and saving to: {OUTPUT_DIR}...")
    print_now("   (Please wait, do not close the terminal...)")
    
    model.save_pretrained_merged(
        OUTPUT_DIR, 
        tokenizer, 
        save_method = "merged_16bit"
    )
    
    print_now("="*50)
    print_now("✅ Merge Complete!")
    print_now(f"📂 Your model is ready at: {os.path.abspath(OUTPUT_DIR)}")
    print_now("="*50)
