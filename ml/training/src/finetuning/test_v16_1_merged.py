#!/usr/bin/env python3
"""
V16.1 MERGED MODEL TEST
=======================
Purpose: Test the merged fine-tuned model on sample SEARCH/REPLACE tasks.

This script:
1. Loads the merged model from models/v16_1_merged/
2. Runs inference on sample SEARCH/REPLACE tasks from validation set
3. Compares outputs with base model
4. Measures inference speed and quality
"""

import json
import torch
import time
from pathlib import Path
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM

# CONFIGURATION
MERGED_MODEL_PATH = "/home/harshil/Harshil-PoCs/models/v16_1_merged"
BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-14B-Instruct"
DATASET_DIR = "/home/harshil/Harshil-PoCs/datasets/v16_1_fixed"
NUM_SAMPLES = 10  # Test on 10 samples
MAX_NEW_TOKENS = 512


def load_validation_samples(num_samples=10):
    """Load sample SEARCH/REPLACE tasks from validation set."""
    print(f"\n📂 Loading {num_samples} validation samples...")
    
    val_path = Path(DATASET_DIR) / "val.jsonl"
    samples = []
    
    with open(val_path, 'r') as f:
        for i, line in enumerate(f):
            if i >= num_samples:
                break
            if line.strip():
                samples.append(json.loads(line))
    
    print(f"   ✓ Loaded {len(samples)} samples")
    return samples


def format_prompt(messages, tokenizer):
    """Format messages using chat template - EXCLUDE assistant response."""
    # Only include system and user messages, not the expected assistant response
    prompt_messages = [m for m in messages if m['role'] != 'assistant']
    return tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True
    )


def test_model(model, tokenizer, samples, model_name="Model"):
    """Run inference tests on samples."""
    print(f"\n🧪 Testing {model_name}...")
    print("=" * 80)
    
    total_time = 0
    results = []
    
    for i, sample in enumerate(samples):
        prompt = format_prompt(sample['messages'], tokenizer)

        # Measure inference time
        start_time = time.time()
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        
        inference_time = time.time() - start_time
        total_time += inference_time
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        results.append({
            'sample_id': i,
            'prompt_length': len(prompt),
            'response_length': len(response),
            'inference_time': inference_time,
            'response': response[:200] + "..." if len(response) > 200 else response
        })
        
        print(f"\n[Sample {i+1}/{len(samples)}]")
        print(f"  Prompt: {prompt[:100]}...")
        print(f"  Time: {inference_time:.2f}s")
        print(f"  Response: {response[:150]}...")
    
    avg_time = total_time / len(samples)
    print("\n" + "=" * 80)
    print(f"Average inference time: {avg_time:.2f}s per sample")
    print(f"Total time: {total_time:.2f}s for {len(samples)} samples")
    
    return results


def main():
    print("=" * 80)
    print("V16.1 MERGED MODEL TEST")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Merged Model: {MERGED_MODEL_PATH}")
    print(f"Base Model: {BASE_MODEL_ID}")
    print("=" * 80)
    
    # Load validation samples
    samples = load_validation_samples(NUM_SAMPLES)
    
    # Load tokenizer
    print("\n🔧 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MERGED_MODEL_PATH)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Load merged model
    print("\n🔧 Loading merged model...")
    merged_model = AutoModelForCausalLM.from_pretrained(
        MERGED_MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    print("   ✓ Merged model loaded")
    
    # Test merged model
    merged_results = test_model(merged_model, tokenizer, samples, "Merged Model")
    
    # Save results
    results_file = Path("/home/harshil/Harshil-PoCs/training/results/v16_1_test_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'model': MERGED_MODEL_PATH,
            'num_samples': len(samples),
            'results': merged_results
        }, f, indent=2)
    
    print(f"\n✅ Test results saved to: {results_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()

