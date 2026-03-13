#!/usr/bin/env python3
"""
V15 Model Testing - Verify Search/Replace Format Generation

Tests:
1. Format Validation - Verify <<<< SEARCH / >>>> REPLACE markers
2. Code Quality - Check generated code is valid
3. Capability Coverage - Test all 7 capabilities
4. Latency - Measure inference time
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Model path
MODEL_PATH = Path("/home/harshil/Harshil-PoCs/models/v15/motadata-coder-v15-merged")

# V15 System Prompt for Search/Replace format
SYSTEM_PROMPT = """You are a senior Motadata engineer. Given a task and files to modify, generate precise Search/Replace blocks.

CRITICAL REQUIREMENTS:
- Generate Search/Replace blocks for ALL files listed in the task
- Use this exact format for each change:

File: path/to/file.java
<<<< SEARCH
[exact code to find - include enough context for unique match]
====
[replacement code]
>>>> REPLACE

- The SEARCH block must contain EXACTLY the code that exists in the file
- Include 2-3 lines of context before/after the change for reliable matching
- Do NOT include line numbers
- Multiple changes to the same file should have multiple SEARCH/REPLACE blocks"""

# Test cases for each capability
TEST_CASES = {
    "direct_generation": {
        "prompt": "Task: Generate a Java method to calculate factorial\n\nFile: Calculator.java\n\nGenerate the complete method using Search/Replace format.",
        "expected_markers": ["<<<< SEARCH", ">>>> REPLACE"]
    },
    "single_file": {
        "prompt": "Task: Add error handling to a division method in Java\n\nFile: Calculator.java\nCurrent code:\npublic int divide(int a, int b) {\n    return a / b;\n}\n\nAdd null/zero checks using Search/Replace format.",
        "expected_markers": ["<<<< SEARCH", ">>>> REPLACE"]
    },
    "tool_use": {
        "prompt": "Task: Add file reading capability to process configuration\n\nFile: ConfigReader.java\n\nAdd methods to read and parse config files using Search/Replace format.",
        "expected_markers": ["<<<< SEARCH", ">>>> REPLACE"]
    },
    "multi_file": {
        "prompt": "Task: Refactor to use dependency injection across files\n\nFiles: Service.java, Repository.java\n\nUpdate both files to use constructor injection using Search/Replace format.",
        "expected_markers": ["<<<< SEARCH", ">>>> REPLACE"]
    },
    "code_review": {
        "prompt": "Task: Review and optimize this Java code for performance\n\nFile: DataProcessor.java\nCurrent: Uses nested loops for data processing\n\nOptimize using Search/Replace format.",
        "expected_markers": ["<<<< SEARCH", ">>>> REPLACE"]
    },
    "file_creation": {
        "prompt": "Task: Create a new Java utility class for string manipulation\n\nFile: StringUtils.java\n\nCreate utility methods using Search/Replace format.",
        "expected_markers": ["<<<< SEARCH", ">>>> REPLACE"]
    },
    "refactoring": {
        "prompt": "Task: Refactor this Java method to use streams instead of loops\n\nFile: DataFilter.java\nCurrent: Uses for loops to filter data\n\nRefactor to use streams using Search/Replace format.",
        "expected_markers": ["<<<< SEARCH", ">>>> REPLACE"]
    }
}

def load_model():
    """Load v15 model and tokenizer"""
    print("Loading v15 model...")
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
    model = AutoModelForCausalLM.from_pretrained(
        str(MODEL_PATH),
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    model.eval()
    print("✓ Model loaded")
    return model, tokenizer

def test_format_validation(output: str) -> Tuple[bool, str]:
    """Verify Search/Replace format markers"""
    has_search = "<<<< SEARCH" in output
    has_replace = ">>>> REPLACE" in output
    
    if has_search and has_replace:
        return True, "✓ Format valid"
    return False, f"✗ Missing markers (SEARCH: {has_search}, REPLACE: {has_replace})"

def test_code_quality(output: str) -> Tuple[bool, str]:
    """Check if generated code looks valid"""
    # Check for basic code patterns
    has_code = any(pattern in output for pattern in [
        "public ", "private ", "def ", "class ", "function ",
        "return ", "if ", "for ", "while "
    ])
    
    if has_code:
        return True, "✓ Code patterns detected"
    return False, "✗ No code patterns found"

def test_inference(model, tokenizer, prompt: str, max_length: int = 512) -> str:
    """Run inference on test prompt with system prompt"""
    # Format with system prompt
    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"

    inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)

    start_time = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
    latency = time.time() - start_time

    output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return output, latency

def main():
    print("=" * 80)
    print("V15 MODEL TESTING - SEARCH/REPLACE FORMAT VALIDATION")
    print("=" * 80)
    print()
    
    # Load model
    model, tokenizer = load_model()
    
    # Test results
    results = {
        "total_tests": len(TEST_CASES),
        "passed": 0,
        "failed": 0,
        "latencies": [],
        "details": {}
    }
    
    # Run tests
    for capability, test_case in TEST_CASES.items():
        print(f"\nTesting {capability.upper()}...")
        print("-" * 60)
        
        try:
            # Run inference
            output, latency = test_inference(model, tokenizer, test_case["prompt"])
            results["latencies"].append(latency)
            
            # Test format
            format_valid, format_msg = test_format_validation(output)
            print(f"  Format: {format_msg}")
            
            # Test code quality
            code_valid, code_msg = test_code_quality(output)
            print(f"  Quality: {code_msg}")
            
            # Overall result
            if format_valid and code_valid:
                results["passed"] += 1
                print(f"  Result: ✓ PASSED")
            else:
                results["failed"] += 1
                print(f"  Result: ✗ FAILED")
            
            print(f"  Latency: {latency:.2f}s")
            
            results["details"][capability] = {
                "format_valid": format_valid,
                "code_valid": code_valid,
                "latency": latency
            }
            
        except Exception as e:
            results["failed"] += 1
            print(f"  ✗ ERROR: {str(e)}")
            results["details"][capability] = {"error": str(e)}
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Pass Rate: {results['passed']/results['total_tests']*100:.1f}%")
    
    if results["latencies"]:
        avg_latency = sum(results["latencies"]) / len(results["latencies"])
        print(f"Average Latency: {avg_latency:.2f}s")
    
    # Save results
    results_file = Path("training/artifacts/v15_test_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to {results_file}")
    
    return results["passed"] == results["total_tests"]

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

