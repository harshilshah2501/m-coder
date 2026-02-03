"""
Evaluate Coder Agent Performance

Measures:
- Latency (time to generate code)
- Token usage
- Code quality metrics
- Success rate
"""

import asyncio
import json
import sys
import os
import time
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.agents.coder_agent import CoderAgent

async def evaluate_coder_agent():
    """Evaluate Coder Agent performance"""
    
    print("=" * 80)
    print("Coder Agent Performance Evaluation")
    print("=" * 80)
    
    agent = CoderAgent()
    
    # Multiple test cases for statistical analysis
    test_cases = [
        {
            "name": "REST Endpoint",
            "file_path": "src/main/java/com/motadata/api/UserAPI.java",
            "file_type": "NEW",
            "requirements": {
                "functional": ["Create REST endpoint for user registration"],
                "non_functional": ["Response time < 100ms"]
            },
            "context": {"retrieved_patterns": [], "retrieved_examples": []}
        },
        {
            "name": "Event Handler",
            "file_path": "src/main/java/com/motadata/events/UserEventHandler.java",
            "file_type": "NEW",
            "requirements": {
                "functional": ["Handle user creation events"],
                "non_functional": ["Process 1000 events/sec"]
            },
            "context": {"retrieved_patterns": [], "retrieved_examples": []}
        },
        {
            "name": "Database Service",
            "file_path": "src/main/java/com/motadata/db/UserService.java",
            "file_type": "NEW",
            "requirements": {
                "functional": ["Query users by email", "Create new user"],
                "non_functional": ["Query latency < 50ms"]
            },
            "context": {"retrieved_patterns": [], "retrieved_examples": []}
        }
    ]
    
    metrics = {
        "latencies": [],
        "code_lengths": [],
        "success_count": 0,
        "failure_count": 0,
        "results": []
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['name']}...", end=" ", flush=True)
        
        start_time = time.time()
        try:
            result = await agent.run(test_case)
            elapsed = time.time() - start_time
            
            if result['status'] == 'SUCCESS':
                metrics["latencies"].append(elapsed)
                metrics["code_lengths"].append(len(result.get('generated_code', '')))
                metrics["success_count"] += 1
                print(f"✅ {elapsed:.2f}s")
            else:
                metrics["failure_count"] += 1
                print(f"❌ Failed")
                
            metrics["results"].append({
                "test": test_case['name'],
                "status": result['status'],
                "latency": elapsed,
                "code_length": len(result.get('generated_code', ''))
            })
            
        except Exception as e:
            metrics["failure_count"] += 1
            print(f"❌ Error: {str(e)[:50]}")
            metrics["results"].append({
                "test": test_case['name'],
                "status": "ERROR",
                "error": str(e)
            })
    
    # Calculate statistics
    print("\n" + "=" * 80)
    print("PERFORMANCE METRICS")
    print("=" * 80)
    
    if metrics["latencies"]:
        print(f"\n⏱️  Latency (seconds):")
        print(f"   Min:     {min(metrics['latencies']):.3f}s")
        print(f"   Max:     {max(metrics['latencies']):.3f}s")
        print(f"   Mean:    {statistics.mean(metrics['latencies']):.3f}s")
        print(f"   Median:  {statistics.median(metrics['latencies']):.3f}s")
        print(f"   StdDev:  {statistics.stdev(metrics['latencies']):.3f}s" if len(metrics['latencies']) > 1 else "")
    
    if metrics["code_lengths"]:
        print(f"\n📝 Code Length (characters):")
        print(f"   Min:     {min(metrics['code_lengths'])} chars")
        print(f"   Max:     {max(metrics['code_lengths'])} chars")
        print(f"   Mean:    {statistics.mean(metrics['code_lengths']):.0f} chars")
        print(f"   Median:  {statistics.median(metrics['code_lengths']):.0f} chars")
    
    total = metrics["success_count"] + metrics["failure_count"]
    success_rate = (metrics["success_count"] / total * 100) if total > 0 else 0
    print(f"\n✅ Success Rate: {success_rate:.1f}% ({metrics['success_count']}/{total})")
    
    # Save results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    print(json.dumps(metrics["results"], indent=2))
    
    # Save to file
    with open("logs/coder_agent_evaluation.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "metrics": {
                "latency_stats": {
                    "min": min(metrics['latencies']) if metrics['latencies'] else 0,
                    "max": max(metrics['latencies']) if metrics['latencies'] else 0,
                    "mean": statistics.mean(metrics['latencies']) if metrics['latencies'] else 0,
                    "median": statistics.median(metrics['latencies']) if metrics['latencies'] else 0,
                },
                "code_length_stats": {
                    "min": min(metrics['code_lengths']) if metrics['code_lengths'] else 0,
                    "max": max(metrics['code_lengths']) if metrics['code_lengths'] else 0,
                    "mean": statistics.mean(metrics['code_lengths']) if metrics['code_lengths'] else 0,
                },
                "success_rate": success_rate,
                "success_count": metrics["success_count"],
                "failure_count": metrics["failure_count"]
            },
            "results": metrics["results"]
        }, f, indent=2)
    
    print("\n✅ Results saved to logs/coder_agent_evaluation.json")
    
    await agent.close()
    return metrics["failure_count"] == 0

if __name__ == "__main__":
    success = asyncio.run(evaluate_coder_agent())
    sys.exit(0 if success else 1)

