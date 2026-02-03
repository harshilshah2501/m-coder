"""
Evaluate Format Validator Performance

Measures:
- Validation accuracy
- False positive/negative rates
- Processing speed
"""

import asyncio
import json
import sys
import os
import time
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.agents.format_validator import FormatValidatorAgent

async def evaluate_format_validator():
    """Evaluate Format Validator performance"""
    
    print("=" * 80)
    print("Format Validator Performance Evaluation")
    print("=" * 80)
    
    validator = FormatValidatorAgent()
    
    # Test cases with expected results
    test_cases = [
        ("Valid Block", "<<<< SEARCH\nold\n>>>>\n\n>>>> REPLACE\nnew\n>>>>", True),
        ("Mismatched", "<<<< SEARCH\nold\n>>>>\n\n<<<< SEARCH\nold2\n>>>>", False),
        ("Unclosed", "<<<< SEARCH\nold\n\n>>>> REPLACE\nnew", False),
        ("Identical", "<<<< SEARCH\nsame\n>>>>\n\n>>>> REPLACE\nsame\n>>>>", False),
        ("Unbalanced Fence", "```java\ncode", False),
        ("Valid Fence", "```java\ncode\n```", True),
        ("Multiple Valid", "<<<< SEARCH\na\n>>>>\n\n>>>> REPLACE\nb\n>>>>\n\n<<<< SEARCH\nc\n>>>>\n\n>>>> REPLACE\nd\n>>>>", True),
        ("Nested Blocks", "<<<< SEARCH\n<<<< SEARCH\nnested\n>>>>\n>>>>\n\n>>>> REPLACE\nnew\n>>>>", False),
    ]
    
    metrics = {
        "latencies": [],
        "true_positives": 0,
        "true_negatives": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "results": []
    }
    
    for i, (name, code, should_be_valid) in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {name}...", end=" ", flush=True)
        
        start_time = time.time()
        state = {
            "generated_code": code,
            "file_path": "test.java",
            "file_type": "NEW"
        }
        
        result = await validator.run(state)
        elapsed = time.time() - start_time
        
        is_valid = result['status'] == 'VALID'
        metrics["latencies"].append(elapsed)
        
        # Calculate accuracy
        if is_valid == should_be_valid:
            if is_valid:
                metrics["true_positives"] += 1
                print("✅ TP")
            else:
                metrics["true_negatives"] += 1
                print("✅ TN")
        else:
            if is_valid:
                metrics["false_positives"] += 1
                print("❌ FP")
            else:
                metrics["false_negatives"] += 1
                print("❌ FN")
        
        metrics["results"].append({
            "test": name,
            "expected_valid": should_be_valid,
            "actual_valid": is_valid,
            "latency": elapsed,
            "error_count": result['error_count']
        })
    
    # Calculate statistics
    print("\n" + "=" * 80)
    print("PERFORMANCE METRICS")
    print("=" * 80)
    
    total = len(test_cases)
    correct = metrics["true_positives"] + metrics["true_negatives"]
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"\n📊 Accuracy: {accuracy:.1f}% ({correct}/{total})")
    print(f"   TP: {metrics['true_positives']} | TN: {metrics['true_negatives']}")
    print(f"   FP: {metrics['false_positives']} | FN: {metrics['false_negatives']}")
    
    if metrics["latencies"]:
        print(f"\n⏱️  Latency (ms):")
        latencies_ms = [l * 1000 for l in metrics["latencies"]]
        print(f"   Min:    {min(latencies_ms):.2f}ms")
        print(f"   Max:    {max(latencies_ms):.2f}ms")
        print(f"   Mean:   {statistics.mean(latencies_ms):.2f}ms")
        print(f"   Median: {statistics.median(latencies_ms):.2f}ms")
    
    # Save results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    print(json.dumps(metrics["results"], indent=2))
    
    with open("logs/format_validator_evaluation.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "metrics": {
                "accuracy": accuracy,
                "true_positives": metrics["true_positives"],
                "true_negatives": metrics["true_negatives"],
                "false_positives": metrics["false_positives"],
                "false_negatives": metrics["false_negatives"],
                "latency_stats": {
                    "min_ms": min(latencies_ms) if latencies_ms else 0,
                    "max_ms": max(latencies_ms) if latencies_ms else 0,
                    "mean_ms": statistics.mean(latencies_ms) if latencies_ms else 0,
                }
            },
            "results": metrics["results"]
        }, f, indent=2)
    
    print("\n✅ Results saved to logs/format_validator_evaluation.json")
    
    return metrics["false_positives"] == 0 and metrics["false_negatives"] == 0

if __name__ == "__main__":
    success = asyncio.run(evaluate_format_validator())
    sys.exit(0 if success else 1)

