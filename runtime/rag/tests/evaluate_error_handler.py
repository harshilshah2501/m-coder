"""
Evaluate Error Handler Performance

Measures:
- Error detection accuracy
- Fix success rate
- Processing latency
"""

import asyncio
import json
import sys
import os
import time
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.agents.error_handler import ErrorHandlerAgent

async def evaluate_error_handler():
    """Evaluate Error Handler performance"""
    
    print("=" * 80)
    print("Error Handler Performance Evaluation")
    print("=" * 80)
    
    agent = ErrorHandlerAgent()
    
    # Test cases: (name, code, has_errors)
    test_cases = [
        ("Valid Code", "public class Test { public void run() { } }", False),
        ("Unmatched Braces 1", "public class Test { public void run() { }", True),
        ("Unmatched Braces 2", "public class Test { public void run() { } } }", True),
        ("Valid Complex", """public class UserAPI {
    private String email;
    public UserAPI(String email) { this.email = email; }
    public String getEmail() { return email; }
}""", False),
        ("Missing Brace", """public class UserAPI {
    public void register(String email) {
        System.out.println(email);
}""", True),
        ("Extra Brace", """public class UserAPI {
    public void register(String email) {
        System.out.println(email);
    }
}}""", True),
    ]
    
    metrics = {
        "latencies": [],
        "detection_correct": 0,
        "detection_incorrect": 0,
        "fix_attempts": 0,
        "fix_success": 0,
        "results": []
    }
    
    for i, (name, code, has_errors) in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {name}...", end=" ", flush=True)
        
        start_time = time.time()
        state = {
            "generated_code": code,
            "file_path": "test.java"
        }
        
        result = await agent.run(state)
        elapsed = time.time() - start_time
        
        detected_errors = result['status'] != 'NO_ERRORS'
        metrics["latencies"].append(elapsed)
        
        # Check detection accuracy
        if detected_errors == has_errors:
            metrics["detection_correct"] += 1
            print("✅", end=" ")
        else:
            metrics["detection_incorrect"] += 1
            print("❌", end=" ")
        
        # Check fix success
        if detected_errors and result['status'] == 'FIXED':
            metrics["fix_attempts"] += 1
            metrics["fix_success"] += 1
            print("FIXED")
        elif detected_errors:
            metrics["fix_attempts"] += 1
            print("UNFIXED")
        else:
            print("OK")
        
        metrics["results"].append({
            "test": name,
            "has_errors": has_errors,
            "detected": detected_errors,
            "status": result['status'],
            "latency": elapsed,
            "fixes": len(result.get('fixes_applied', []))
        })
    
    # Calculate statistics
    print("\n" + "=" * 80)
    print("PERFORMANCE METRICS")
    print("=" * 80)
    
    total = len(test_cases)
    detection_accuracy = (metrics["detection_correct"] / total * 100) if total > 0 else 0
    fix_success_rate = (metrics["fix_success"] / metrics["fix_attempts"] * 100) if metrics["fix_attempts"] > 0 else 0
    
    print(f"\n🎯 Detection Accuracy: {detection_accuracy:.1f}% ({metrics['detection_correct']}/{total})")
    print(f"🔧 Fix Success Rate: {fix_success_rate:.1f}% ({metrics['fix_success']}/{metrics['fix_attempts']})")
    
    if metrics["latencies"]:
        latencies_ms = [l * 1000 for l in metrics["latencies"]]
        print(f"\n⏱️  Latency (ms):")
        print(f"   Min:    {min(latencies_ms):.2f}ms")
        print(f"   Max:    {max(latencies_ms):.2f}ms")
        print(f"   Mean:   {statistics.mean(latencies_ms):.2f}ms")
        print(f"   Median: {statistics.median(latencies_ms):.2f}ms")
    
    # Save results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    print(json.dumps(metrics["results"], indent=2))
    
    with open("logs/error_handler_evaluation.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "metrics": {
                "detection_accuracy": detection_accuracy,
                "fix_success_rate": fix_success_rate,
                "latency_stats": {
                    "min_ms": min(latencies_ms) if latencies_ms else 0,
                    "max_ms": max(latencies_ms) if latencies_ms else 0,
                    "mean_ms": statistics.mean(latencies_ms) if latencies_ms else 0,
                }
            },
            "results": metrics["results"]
        }, f, indent=2)
    
    print("\n✅ Results saved to logs/error_handler_evaluation.json")
    
    return metrics["detection_incorrect"] == 0

if __name__ == "__main__":
    success = asyncio.run(evaluate_error_handler())
    sys.exit(0 if success else 1)

