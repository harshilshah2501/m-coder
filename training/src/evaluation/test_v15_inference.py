#!/usr/bin/env python3
"""
V15 Inference Testing
Test the merged model on diverse prompts
"""

import torch
import time
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path

# Configuration
MERGED_MODEL_PATH = "training/results/v15_merged"

# Test cases covering 7 capabilities
TEST_CASES = {
    "direct_generation": {
        "prompt": "Generate a Java method to calculate factorial of a number",
        "max_tokens": 256
    },
    "single_file": {
        "prompt": "File: Calculator.java\nAdd error handling for division by zero",
        "max_tokens": 256
    },
    "tool_use": {
        "prompt": "Use file operations to read and parse a JSON configuration file",
        "max_tokens": 256
    },
    "multi_file": {
        "prompt": "Refactor code across multiple files to use dependency injection pattern",
        "max_tokens": 256
    },
    "code_review": {
        "prompt": "Review this Java code for performance issues and suggest improvements",
        "max_tokens": 256
    },
    "file_creation": {
        "prompt": "Create a new Java class for managing database connections",
        "max_tokens": 256
    },
    "refactoring": {
        "prompt": "Refactor this code to improve readability and maintainability",
        "max_tokens": 256
    }
}

def load_model():
    """Load the merged model"""
    print("🔧 Loading merged model...")
    model = AutoModelForCausalLM.from_pretrained(
        MERGED_MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(MERGED_MODEL_PATH)
    print("✅ Model loaded")
    return model, tokenizer

def test_inference(model, tokenizer, prompt, max_tokens=256):
    """Run inference on a prompt"""
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    start_time = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
    latency = time.time() - start_time
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response, latency

def main():
    print("="*80)
    print("V15 INFERENCE TESTING")
    print("="*80)
    print()
    
    # Load model
    model, tokenizer = load_model()
    
    # Run tests
    results = {}
    print("🧪 Running inference tests...\n")
    
    for i, (capability, test) in enumerate(TEST_CASES.items(), 1):
        print(f"[{i}/{len(TEST_CASES)}] Testing {capability}...", end=" ", flush=True)
        
        try:
            response, latency = test_inference(
                model, tokenizer, 
                test["prompt"], 
                test["max_tokens"]
            )
            
            results[capability] = {
                "status": "✅ PASS",
                "latency_ms": latency * 1000,
                "response_length": len(response),
                "response_preview": response[:200]
            }
            
            print(f"✅ ({latency:.2f}s)")
        except Exception as e:
            results[capability] = {
                "status": "❌ FAIL",
                "error": str(e)
            }
            print(f"❌ Error: {str(e)[:50]}")
    
    # Print summary
    print("\n" + "="*80)
    print("INFERENCE TEST RESULTS")
    print("="*80)
    
    passed = sum(1 for r in results.values() if "PASS" in r["status"])
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"\nCapability Results:")
    for capability, result in results.items():
        status = result["status"]
        if "PASS" in status:
            latency = result["latency_ms"]
            print(f"  {capability:20} {status} ({latency:.0f}ms)")
        else:
            print(f"  {capability:20} {status}")
    
    print("\n" + "="*80)
    print("✅ INFERENCE TESTING COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()

