#!/usr/bin/env python3
"""
V16 Inference Testing
Test the merged model on diverse prompts covering all 7 capabilities
"""

import torch
import time
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path

# Configuration
MERGED_MODEL_PATH = "/home/harshil/Harshil-PoCs/training/artifacts/results/v16_merged"
OUTPUT_FILE = "/home/harshil/Harshil-PoCs/training/artifacts/results/v16_evaluation/v16_inference_results.json"

# Test cases covering 7 capabilities
TEST_CASES = {
    "direct_generation": {
        "prompt": "Generate a Java method to calculate factorial of a number",
        "max_tokens": 256,
        "category": "Direct Generation"
    },
    "single_file": {
        "prompt": "File: Calculator.java\nAdd error handling for division by zero",
        "max_tokens": 256,
        "category": "Single-File Edit"
    },
    "tool_use": {
        "prompt": "Use file operations to read and parse a JSON configuration file",
        "max_tokens": 256,
        "category": "Tool Use"
    },
    "multi_file": {
        "prompt": "Refactor code across multiple files to use dependency injection pattern",
        "max_tokens": 256,
        "category": "Multi-File Edit"
    },
    "code_review": {
        "prompt": "Review this Java code for performance issues and suggest improvements",
        "max_tokens": 256,
        "category": "Code Review"
    },
    "file_creation": {
        "prompt": "Create a new Java class for managing database connections",
        "max_tokens": 256,
        "category": "File Creation"
    },
    "refactoring": {
        "prompt": "Refactor this code to improve readability and maintainability",
        "max_tokens": 256,
        "category": "Refactoring"
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
    print("V16 INFERENCE TESTING")
    print("="*80)
    print()
    
    # Load model
    model, tokenizer = load_model()
    
    # Run tests
    results = {}
    latencies = []
    
    print("🧪 Running inference tests...\n")
    
    for i, (capability, test) in enumerate(TEST_CASES.items(), 1):
        print(f"[{i}/{len(TEST_CASES)}] Testing {test['category']}...", end=" ", flush=True)
        
        try:
            response, latency = test_inference(
                model, tokenizer, 
                test["prompt"], 
                test["max_tokens"]
            )
            
            results[capability] = {
                "status": "PASS",
                "category": test['category'],
                "latency_ms": latency * 1000,
                "response_length": len(response),
                "response_preview": response[:200]
            }
            
            latencies.append(latency)
            print(f"✅ ({latency:.2f}s)")
        except Exception as e:
            results[capability] = {
                "status": "FAIL",
                "category": test['category'],
                "error": str(e)
            }
            print(f"❌ Error: {str(e)[:50]}")
    
    # Print summary
    print("\n" + "="*80)
    print("INFERENCE TEST RESULTS")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r["status"] == "PASS")
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"\nCapability Results:")
    for capability, result in results.items():
        status = "✅ PASS" if result["status"] == "PASS" else "❌ FAIL"
        if result["status"] == "PASS":
            latency = result["latency_ms"]
            print(f"  {result['category']:<25} {status} ({latency:.0f}ms)")
        else:
            print(f"  {result['category']:<25} {status}")
    
    # Performance metrics
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print(f"\n📊 Performance Metrics:")
        print(f"  Average Latency: {avg_latency*1000:.0f}ms")
        print(f"  Min Latency: {min_latency*1000:.0f}ms")
        print(f"  Max Latency: {max_latency*1000:.0f}ms")
    
    # Save results
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to {OUTPUT_FILE}")
    
    print("\n" + "="*80)
    print("✅ INFERENCE TESTING COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()

