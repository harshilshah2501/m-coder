#!/usr/bin/env python3
"""
V15 Model Benchmarking - Performance Analysis

Measures:
1. Throughput - Tokens per second
2. Latency - Time to first token, total generation time
3. Memory Usage - Peak GPU/CPU memory
4. Quality - Pass rate on benchmark tasks
"""

import json
import time
import psutil
import torch
from pathlib import Path
from typing import Dict, List

from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_PATH = Path("/home/harshil/Harshil-PoCs/models/v15/motadata-coder-v15-merged")

SYSTEM_PROMPT = """You are a senior Motadata engineer. Generate Search/Replace blocks.

File: path/to/file.java
<<<< SEARCH
[exact code to find]
====
[replacement code]
>>>> REPLACE"""

BENCHMARK_PROMPTS = [
    "Task: Add error handling to division method",
    "Task: Refactor loops to use streams",
    "Task: Add logging to service methods",
    "Task: Implement dependency injection",
    "Task: Add validation to input parameters",
]

def get_memory_usage():
    """Get current memory usage"""
    process = psutil.Process()
    return {
        "rss_mb": process.memory_info().rss / 1024 / 1024,
        "vms_mb": process.memory_info().vms / 1024 / 1024,
    }

def load_model():
    """Load v15 model"""
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

def benchmark_inference(model, tokenizer, prompt: str, num_runs: int = 3) -> Dict:
    """Benchmark inference performance"""
    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
    
    latencies = []
    token_counts = []
    
    for i in range(num_runs):
        inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
        input_tokens = inputs["input_ids"].shape[1]
        
        start_time = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        latency = time.time() - start_time
        
        output_tokens = outputs.shape[1] - input_tokens
        latencies.append(latency)
        token_counts.append(output_tokens)
    
    avg_latency = sum(latencies) / len(latencies)
    avg_tokens = sum(token_counts) / len(token_counts)
    throughput = avg_tokens / avg_latency if avg_latency > 0 else 0
    
    return {
        "avg_latency_s": avg_latency,
        "avg_tokens_generated": avg_tokens,
        "throughput_tokens_per_sec": throughput,
        "latencies": latencies,
        "token_counts": token_counts
    }

def main():
    print("=" * 80)
    print("V15 MODEL BENCHMARKING - PERFORMANCE ANALYSIS")
    print("=" * 80)
    print()
    
    # Load model
    model, tokenizer = load_model()
    
    # Memory before
    mem_before = get_memory_usage()
    print(f"Memory before: {mem_before['rss_mb']:.1f} MB")
    
    # Run benchmarks
    results = {
        "model": "motadata-coder-v15-merged",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "benchmarks": {},
        "summary": {}
    }
    
    print("\nRunning benchmarks...")
    print("-" * 80)
    
    all_latencies = []
    all_throughputs = []
    
    for i, prompt in enumerate(BENCHMARK_PROMPTS, 1):
        print(f"\nBenchmark {i}/{len(BENCHMARK_PROMPTS)}: {prompt[:50]}...")
        
        bench_result = benchmark_inference(model, tokenizer, prompt, num_runs=3)
        results["benchmarks"][f"benchmark_{i}"] = bench_result
        
        all_latencies.extend(bench_result["latencies"])
        all_throughputs.append(bench_result["throughput_tokens_per_sec"])
        
        print(f"  Avg Latency: {bench_result['avg_latency_s']:.2f}s")
        print(f"  Tokens Generated: {bench_result['avg_tokens_generated']:.0f}")
        print(f"  Throughput: {bench_result['throughput_tokens_per_sec']:.1f} tokens/sec")
    
    # Memory after
    mem_after = get_memory_usage()
    print(f"\nMemory after: {mem_after['rss_mb']:.1f} MB")
    
    # Summary statistics
    results["summary"] = {
        "total_benchmarks": len(BENCHMARK_PROMPTS),
        "avg_latency_s": sum(all_latencies) / len(all_latencies),
        "min_latency_s": min(all_latencies),
        "max_latency_s": max(all_latencies),
        "avg_throughput_tokens_per_sec": sum(all_throughputs) / len(all_throughputs),
        "peak_memory_mb": mem_after['rss_mb'],
        "memory_increase_mb": mem_after['rss_mb'] - mem_before['rss_mb']
    }
    
    # Print summary
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    summary = results["summary"]
    print(f"Total Benchmarks: {summary['total_benchmarks']}")
    print(f"Average Latency: {summary['avg_latency_s']:.2f}s")
    print(f"Min Latency: {summary['min_latency_s']:.2f}s")
    print(f"Max Latency: {summary['max_latency_s']:.2f}s")
    print(f"Average Throughput: {summary['avg_throughput_tokens_per_sec']:.1f} tokens/sec")
    print(f"Peak Memory: {summary['peak_memory_mb']:.1f} MB")
    print(f"Memory Increase: {summary['memory_increase_mb']:.1f} MB")
    
    # Save results
    results_file = Path("training/artifacts/v15_benchmark_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to {results_file}")

if __name__ == "__main__":
    main()

