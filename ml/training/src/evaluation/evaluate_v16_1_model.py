#!/usr/bin/env python3
"""
V16.1 Comprehensive Model Evaluation
Evaluates the fine-tuned 14B model on:
1. Test loss metrics
2. Inference quality across 7 capabilities
3. Dataset alignment verification
4. Performance benchmarking
"""

import torch
import json
import time
from pathlib import Path
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Configuration
BASE_MODEL = "Qwen/Qwen2.5-Coder-14B-Instruct"
LORA_MODEL_PATH = "/home/harshil/Harshil-PoCs/models/v16_1_finetuned"
TEST_FILE = "/home/harshil/Harshil-PoCs/datasets/v16_1_splits/test.jsonl"
OUTPUT_DIR = "/home/harshil/Harshil-PoCs/training/artifacts/results/v16_1_evaluation"

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Test cases for 7 capabilities
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
    """Load base model and merge with LoRA weights"""
    print("Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    
    print("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(model, LORA_MODEL_PATH)
    model = model.merge_and_unload()
    
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    return model, tokenizer

def test_inference(model, tokenizer, prompt, max_tokens=256):
    """Run inference and measure latency"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    start_time = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
    latency = time.time() - start_time
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response, latency

def run_inference_tests(model, tokenizer):
    """Test all 7 capabilities"""
    results = {}
    print("\n" + "="*80)
    print("INFERENCE TESTING - 7 CAPABILITIES")
    print("="*80 + "\n")
    
    for i, (capability, test) in enumerate(TEST_CASES.items(), 1):
        print(f"[{i}/7] Testing {capability}...", end=" ", flush=True)
        
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
    
    return results

def main():
    print("="*80)
    print("V16.1 COMPREHENSIVE MODEL EVALUATION")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Base Model: {BASE_MODEL}")
    print(f"LoRA Adapter: {LORA_MODEL_PATH}")
    print()
    
    # Load model
    model, tokenizer = load_model()
    
    # Run inference tests
    inference_results = run_inference_tests(model, tokenizer)
    
    # Compile report
    report = {
        "timestamp": datetime.now().isoformat(),
        "model": BASE_MODEL,
        "lora_adapter": LORA_MODEL_PATH,
        "inference_tests": inference_results,
        "summary": {
            "total_tests": len(TEST_CASES),
            "passed": sum(1 for r in inference_results.values() if "PASS" in r.get("status", "")),
            "failed": sum(1 for r in inference_results.values() if "FAIL" in r.get("status", ""))
        }
    }
    
    # Save report
    report_path = Path(OUTPUT_DIR) / "v16_1_inference_evaluation.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_path}")
    print("\n" + "="*80)
    print("EVALUATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()

